import pandas as pd
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = FastAPI()

# ---------- global variable to store the uploaded CSV data
uploaded_csv_data = None

# -------------- Function to read CSV data
def read_csv_data(content: bytes):
    try:
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV data: {str(e)}")

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    global uploaded_csv_data
    if file.filename.endswith('.csv'):
        content = await file.read()
        try:
            # -------------- Read CSV file
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            
            #----------- Limit to 30 columns
            df = df.iloc[:, :30]
            
            # ----------- Limit to 3000 rows
            df = df.iloc[:3000, :]
            
            # ------ Update uploaded_csv_data
            uploaded_csv_data = df
            
            # --------------- Drop columns with string values
            uploaded_csv_data = uploaded_csv_data.select_dtypes(exclude=['object'])
            
            # ----------- Get rows and columns count
            rows, columns = uploaded_csv_data.shape
            
            # ------------------- Get summary
            summary = uploaded_csv_data.describe().to_dict()
            
            # ----------------- Count empty cells in each column
            empty_cells_count = uploaded_csv_data.isnull().sum().to_dict()
            for column, empty_count in empty_cells_count.items():
                summary[column]['empty_cells'] = empty_count
            
            # ------------- Replace NaN values with a string representation
            uploaded_csv_data = uploaded_csv_data.fillna("NaN")
            
            # -------------------- Retrieve data of each column
            column_data = {}
            for column in uploaded_csv_data.columns:
                column_data[column] = uploaded_csv_data[column].tolist()

            return {"rows": rows, "columns": columns, "summary": summary, "column_data": column_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")



# ------------- scatter Plot
@app.post("/plot/scatter/")
async def plot_scatter_chart(x_column: str, y_column: str):
    global uploaded_csv_data
    if uploaded_csv_data is None:
        raise HTTPException(status_code=400, detail="CSV file not uploaded")
    
    if x_column not in uploaded_csv_data.columns or y_column not in uploaded_csv_data.columns:
        raise HTTPException(status_code=400, detail="X or Y column not found in CSV file")
    
    fig = go.Figure(data=go.Scatter(x=uploaded_csv_data[x_column], y=uploaded_csv_data[y_column], mode='markers'))
    fig.update_layout(title=f"Scatter Plot ({x_column} vs {y_column})")
    fig.update_xaxes(title_text=x_column)
    fig.update_yaxes(title_text=y_column)
    
    return fig.to_json()

# ---------- bar chart
@app.post("/plot/bar/")
async def plot_bar_chart(x_column: str, y_column: str):
    global uploaded_csv_data
    if uploaded_csv_data is None:
        raise HTTPException(status_code=400, detail="CSV file not uploaded")
    
    if x_column not in uploaded_csv_data.columns or y_column not in uploaded_csv_data.columns:
        raise HTTPException(status_code=400, detail="X or Y column not found in CSV file")
    
    fig = go.Figure(data=go.Bar(x=uploaded_csv_data[x_column], y=uploaded_csv_data[y_column]))
    fig.update_layout(title=f"Bar Chart ({y_column} vs {x_column})", xaxis_title=x_column, yaxis_title=y_column)
    
    return fig.to_json()

# ----------- histogram
@app.post("/plot/histogram/")
async def plot_histogram(column_name: str):
    global uploaded_csv_data
    if uploaded_csv_data is None:
        raise HTTPException(status_code=400, detail="CSV file not uploaded")
    
    if column_name not in uploaded_csv_data.columns:
        raise HTTPException(status_code=400, detail="Column not found in CSV file")
    
    fig = go.Figure(data=go.Histogram(x=uploaded_csv_data[column_name]))
    fig.update_layout(title=f"Histogram for {column_name}", xaxis_title=column_name, yaxis_title="Count")
    
    return fig.to_json()

# -------- heatmap
@app.post("/plot/heatmap/")
async def plot_heatmap(x_column: str, y_column: str):
    global uploaded_csv_data
    if uploaded_csv_data is None:
        raise HTTPException(status_code=400, detail="CSV file not uploaded")
    
    if x_column not in uploaded_csv_data.columns or y_column not in uploaded_csv_data.columns:
        raise HTTPException(status_code=400, detail="X or Y column not found in CSV file")
    
    pivot_table = uploaded_csv_data.pivot_table(values=y_column, index=x_column, aggfunc='mean')
    fig = go.Figure(data=go.Heatmap(z=pivot_table.values, x=pivot_table.columns, y=pivot_table.index))
    fig.update_layout(title=f"Heatmap ({y_column} vs {x_column})", xaxis_title=x_column, yaxis_title=y_column)
    
    return fig.to_json()
