#!/opt/anaconda3/bin/python
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import os

# File paths for your data
file_paths = {
    'Day 0 vs Day 7': "/Volumes/TOSHIBA EXT/Yaron's data/horshoebatrun3/Mt. Sinai Data/Day_0_vs_Day_7_differential_expression_results.csv",
    'Day 7 vs Day 13': "/Volumes/TOSHIBA EXT/Yaron's data/horshoebatrun3/Mt. Sinai Data/Day_7_vs_Day_13_differential_expression_results.csv",
    'Day 13 vs Day 17': "/Volumes/TOSHIBA EXT/Yaron's data/horshoebatrun3/results_D17_vs_D13.csv",
    'Day 17 vs Day 23': "/Volumes/TOSHIBA EXT/Yaron's data/horshoebatrun3/results_D23_vs_D17.csv"
}

# Combine datasets
dfs = []
for label, path in file_paths.items():
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    try:
        df = pd.read_csv(path)
        if 'logFC' in df.columns:
            df.rename(columns={'logFC': 'log2FoldChange', 'P.Value': 'pvalue', 'adj.P.Val': 'padj'}, inplace=True)
        if 'Unnamed: 0' in df.columns:
            df.rename(columns={'Unnamed: 0': 'GeneID'}, inplace=True)
        df['Comparison'] = label
        dfs.append(df)
    except Exception as e:
        print(f"Error reading file {path}: {e}")

if not dfs:
    raise ValueError("No valid data files loaded. Please check file paths and formatting.")

combined_df = pd.concat(dfs, ignore_index=True)

# Initialize Dash app
app = Dash(__name__)

# Calculate dynamic range for slider
min_value = combined_df['log2FoldChange'].min() if 'log2FoldChange' in combined_df else -10
max_value = combined_df['log2FoldChange'].max() if 'log2FoldChange' in combined_df else 10

# Layout
app.layout = html.Div([
    html.H1("BIPSCs Differentiation Heatmap"),
    dcc.Dropdown(
        id='metric-selector',
        options=[
            {'label': 'Log2 Fold Change', 'value': 'log2FoldChange'},
            {'label': 'P-value', 'value': 'pvalue'},
            {'label': 'Adjusted P-value', 'value': 'padj'}
        ],
        value='log2FoldChange',
        multi=False,
        placeholder="Select a metric"
    ),
    dcc.Dropdown(
        id='gene-selector',
        options=[{'label': gene, 'value': gene} for gene in combined_df['GeneID'].unique()],
        value=combined_df['GeneID'].unique()[:10],  # Pre-select first 10 genes
        multi=True,
        placeholder="Select genes"
    ),
    dcc.Graph(id='heatmap'),
    dcc.RangeSlider(
        id='scale-slider',
        min=min_value,
        max=max_value,
        step=0.1,
        value=[-2, 2],
        marks={i: f'{i}' for i in range(int(min_value), int(max_value)+1, 2)}
    ),
    html.Div(id='slider-output', style={'margin-top': 20})
])

# Callbacks
@app.callback(
    [Output('heatmap', 'figure'),
     Output('slider-output', 'children')],
    [Input('metric-selector', 'value'),
     Input('gene-selector', 'value'),
     Input('scale-slider', 'value')]
)
def update_heatmap(selected_metric, selected_genes, scale_range):
    if not selected_genes:
        selected_genes = combined_df['GeneID'].unique()

    # Filter the data for selected genes
    filtered_df = combined_df[combined_df['GeneID'].isin(selected_genes)]
    
    # Pivot the data to use in the heatmap
    heatmap_data = filtered_df.pivot(index='GeneID', columns='Comparison', values=selected_metric)
    heatmap_data = heatmap_data.reindex(selected_genes)  # Re-order rows based on the selected genes

    # Create the heatmap
    fig = px.imshow(
        heatmap_data,
        color_continuous_scale='Viridis',
        aspect='auto',
        title=f"Heatmap for {selected_metric}",
        labels={'color': selected_metric},
        zmin=scale_range[0],  # Use the slider's lower bound
        zmax=scale_range[1]   # Use the slider's upper bound
    )
    
    # Update axis labels
    fig.update_xaxes(title='Comparison')
    fig.update_yaxes(title='GeneID')
    
    # Display the current range on the page
    slider_text = f'Selected Color Scale: {scale_range[0]} to {scale_range[1]}'
    
    return fig, slider_text

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
