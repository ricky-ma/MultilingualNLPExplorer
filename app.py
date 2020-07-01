import base64
import io
import plotly.express as px
import pandas as pd
import umap
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from sklearn.preprocessing import StandardScaler


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def parse_content(content, filename, is_vec):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), header=None)
        elif 'tsv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter='\t', header=None)
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded), header=None)
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    if is_vec:
        df = df.drop(df.columns[0], axis=1)
    else:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
    return df


def parse_contents(list_of_contents, list_of_names):
    for contents, filename in zip(list_of_contents, list_of_names):
        if 'vec' in filename:
            df_vec = parse_content(contents, filename, True)
            print(df_vec.head)
        if 'meta' in filename:
            df_meta = parse_content(contents, filename, False)
            print(df_meta.head)

    # try:
    return load_data(df_vec, df_meta)
    # except Exception as e:
    #     print(e)
    #     return html.Div([
    #         'There was an error processing this file.'
    #     ])


def load_data(df_vec, df_meta):
    reducer = umap.UMAP(n_components=2)
    # reducer = umap.UMAP(n_components=3)

    data = df_vec[df_vec.columns].values
    scaled_data = StandardScaler().fit_transform(data)
    embedding = reducer.fit_transform(scaled_data, y=df_meta['FAQ_id'])

    print(embedding.shape)
    embedding_df = pd.DataFrame(embedding, columns=['x', 'y'])
    # embedding_df = pd.DataFrame(embedding, columns=['x', 'y', 'z'])
    final_df = embedding_df.join(df_meta)
    return make_figure(final_df)


def make_figure(dataframe):
    fig = px.scatter(dataframe, x='x', y='y', color='FAQ_id', hover_name='question')
    # fig = px.scatter_3d(dataframe, x='x', y='y', z='z', color='FAQ_id', hover_name='question')
    return html.Div([
        dcc.Graph(
            id='scatter',
            figure=fig
        )
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(list_of_contents, list_of_names)
        ]
        return children


app.layout = html.Div(children=[
    html.H1(children='Multilingual NLP Explorer'),

    html.Div(children='''
        Exploratory data analysis for multilingual NLP.
    '''),
    html.Hr(),
    dcc.Upload(id='upload-data', children=html.Button('Upload Files'), multiple=True),
    html.Hr(),

    html.Div(id='output-data-upload'),

])

if __name__ == '__main__':
    app.run_server(debug=True)