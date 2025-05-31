import os
import uuid
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory
)
import pandas as pd
import plotly.express as px
import plotly.io as pio

# ------------ Configurações Iniciais ------------

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'supersecretkey'

# Pastas para salvar gráficos e dados
CHARTS_DIR = os.path.join(app.static_folder, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

DATA_DIR = os.path.join(app.static_folder, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


# ------------ Rotas ------------

@app.route('/')
def landing_page():
    return render_template('landing.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """
    state=1 (GET): apenas upload de CSV.
    state=2 (POST /dashboard): pré-leitura do CSV → extrai columns, numeric_cols, unique_values.
    """
    if request.method == 'GET':
        return render_template(
            'index.html',
            state=1,
            columns=None,
            numeric_cols=None,
            unique_values={},      # vazio para state=1
            data_uid=None,
            background_color='#121212',
            selected_template='plotly_dark',
            x_axis=None,
            y_axes=[],
            filter_column1=None,
            filter_value1=None,
            filter_column2=None,
            filter_value2=None,
            charts=None,
            insights=None,
            data_csv_url=None,
            data_xlsx_url=None
        )

    # Se for POST aqui, user enviou o CSV para pré-leitura (state=2)
    file = request.files.get('file')
    if not file:
        flash("Nenhum arquivo foi enviado!", "danger")
        return redirect(url_for('dashboard'))

    uid_data = uuid.uuid4().hex
    csv_filename = f"data_{uid_data}.csv"
    csv_path = os.path.join(DATA_DIR, csv_filename)

    # Tenta ler em UTF-8, se falhar tenta Latin1
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding='latin1')
        except Exception as e2:
            flash(f"Erro ao ler o arquivo CSV: {e2}", "danger")
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"Erro ao ler o arquivo CSV: {e}", "danger")
        return redirect(url_for('dashboard'))

    # Salvar CSV original
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    except Exception as e:
        flash(f"Erro ao salvar o CSV no servidor: {e}", "warning")

    # Extrair colunas e colunas numéricas
    columns_list = list(df.columns)
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

    # Criar dicionário de valores únicos para cada coluna
    unique_values = {}
    for col in columns_list:
        vals = df[col].dropna().unique().tolist()
        unique_values[col] = [str(x) for x in vals]

    # Renderizar state=2
    return render_template(
        'index.html',
        state=2,
        columns=columns_list,
        numeric_cols=numeric_cols,
        unique_values=unique_values,
        data_uid=uid_data,
        background_color='#121212',
        selected_template='plotly_dark',
        x_axis=None,
        y_axes=[],
        filter_column1=None,
        filter_value1=None,
        filter_column2=None,
        filter_value2=None,
        charts=None,
        insights=None,
        data_csv_url=None,
        data_xlsx_url=None
    )


@app.route('/generate_dashboard', methods=['POST'])
def generate_dashboard():
    """
    Recebe as configurações do usuário (cores, template, eixos, filtros),
    aplica os filtros e gera os gráficos (state=3).
    """
    data_uid = request.form.get('data_uid')
    if not data_uid:
        flash("Identificador do CSV não encontrado. Tente enviar o arquivo novamente.", "danger")
        return redirect(url_for('dashboard'))

    csv_filename = f"data_{data_uid}.csv"
    csv_path = os.path.join(DATA_DIR, csv_filename)

    if not os.path.exists(csv_path):
        flash("Arquivo CSV não encontrado no servidor. Envie novamente.", "danger")
        return redirect(url_for('dashboard'))

    # Ler o CSV original salvo
    try:
        df_original = pd.read_csv(csv_path, encoding='utf-8')
    except Exception:
        try:
            df_original = pd.read_csv(csv_path, encoding='latin1')
        except Exception as e:
            flash(f"Erro ao ler o arquivo CSV salvo: {e}", "danger")
            return redirect(url_for('dashboard'))

    # Extrair colunas e numéricas do original
    columns_list = list(df_original.columns)
    numeric_cols = df_original.select_dtypes(include=['float64', 'int64']).columns.tolist()

    # Reconstruir unique_values
    unique_values = {}
    for col in columns_list:
        vals = df_original[col].dropna().unique().tolist()
        unique_values[col] = [str(x) for x in vals]

    # Ler parâmetros do formulário (para repovoar o formulário no template)
    background_color = request.form.get('background_color', '#121212')
    selected_template = request.form.get('selected_template', 'plotly_dark')
    color = request.form.get('color', '#636efa')
    x_axis = request.form.get('x_axis')
    y_axes = request.form.getlist('y_axis')

    filter_column1 = request.form.get('filter_column1')
    filter_value1 = request.form.get('filter_value1')
    filter_column2 = request.form.get('filter_column2')
    filter_value2 = request.form.get('filter_value2')

    # Aplicar até dois filtros ao DataFrame de trabalho
    df = df_original.copy()
    if filter_column1 and filter_value1:
        if filter_column1 in df.columns:
            df = df[df[filter_column1].astype(str) == filter_value1]
        else:
            flash(f"Coluna de filtro 1 '{filter_column1}' não encontrada.", "warning")

    if filter_column2 and filter_value2:
        if filter_column2 in df.columns:
            df = df[df[filter_column2].astype(str) == filter_value2]
        else:
            flash(f"Coluna de filtro 2 '{filter_column2}' não encontrada.", "warning")

    # Garantir que x_axis seja válido
    if not x_axis or x_axis not in df.columns:
        x_axis = df.columns[0]

    # Filtrar apenas y_axes numéricos válidos
    y_axes_valid = [y for y in y_axes if y in df.columns and pd.api.types.is_numeric_dtype(df[y])]
    if not y_axes_valid:
        flash("Selecione ao menos um eixo Y válido (numérico).", "warning")
        # Retornar ao estado 2 com o formulário preenchido
        return render_template(
            'index.html',
            state=2,
            columns=columns_list,
            numeric_cols=numeric_cols,
            unique_values=unique_values,
            data_uid=data_uid,
            background_color=background_color,
            selected_template=selected_template,
            x_axis=x_axis,
            y_axes=[],
            filter_column1=filter_column1,
            filter_value1=filter_value1,
            filter_column2=filter_column2,
            filter_value2=filter_value2,
            charts=None,
            insights=None,
            data_csv_url=None,
            data_xlsx_url=None
        )

    # Salvar CSV filtrado
    filtered_uid = uuid.uuid4().hex
    csv_filtrado_filename = f"data_filtered_{filtered_uid}.csv"
    csv_filtrado_path = os.path.join(DATA_DIR, csv_filtrado_filename)
    try:
        df.to_csv(csv_filtrado_path, index=False, encoding='utf-8-sig')
        data_csv_url = url_for('download_data', filename=csv_filtrado_filename)
    except Exception as e:
        flash(f"Erro ao salvar CSV filtrado: {e}", "warning")
        data_csv_url = None

    # Tentar XLSX filtrado (caso openpyxl instalado)
    xlsx_filtrado_filename = f"data_filtered_{filtered_uid}.xlsx"
    xlsx_filtrado_path = os.path.join(DATA_DIR, xlsx_filtrado_filename)
    data_xlsx_url = None
    try:
        df.to_excel(xlsx_filtrado_path, index=False)
        data_xlsx_url = url_for('download_data', filename=xlsx_filtrado_filename)
    except ImportError:
        # openpyxl não instalado: ignora
        pass
    except Exception as e:
        flash(f"Erro ao salvar XLSX filtrado: {e}", "warning")
        data_xlsx_url = None

    # Gerar gráficos para cada y_axis selecionado
    charts = []
    insights = []

    def unique_chart_filename(base_name):
        uid = uuid.uuid4().hex
        return f"{base_name}_{uid}.html"

    for y_axis in y_axes_valid:
        # 1) Gráfico de Barras
        chart_bar = px.bar(
            df,
            x=x_axis,
            y=y_axis,
            title=f"Barras: {x_axis} vs {y_axis}",
            color_discrete_sequence=[color]
        )
        chart_bar.update_layout(
            template=selected_template,
            yaxis_tickformat=".0f"    # força valor inteiro (sem M)
        )
        chart1_html = pio.to_html(chart_bar, full_html=False)
        filename1 = unique_chart_filename("chart_bar")
        with open(os.path.join(CHARTS_DIR, filename1), "w", encoding="utf-8") as f:
            f.write(chart1_html)
        charts.append({"html": chart1_html, "url": url_for('download_chart', filename=filename1)})
        insights.append(f"Barras ({y_axis}): {df[y_axis].describe().to_dict()}")

        # 2) Gráfico de Linhas
        chart_line = px.line(
            df,
            x=x_axis,
            y=y_axis,
            title=f"Linhas: {x_axis} vs {y_axis}",
            markers=True,
            color_discrete_sequence=[color]
        )
        chart_line.update_layout(
            template=selected_template,
            yaxis_tickformat=".0f"
        )
        chart2_html = pio.to_html(chart_line, full_html=False)
        filename2 = unique_chart_filename("chart_line")
        with open(os.path.join(CHARTS_DIR, filename2), "w", encoding="utf-8") as f:
            f.write(chart2_html)
        charts.append({"html": chart2_html, "url": url_for('download_chart', filename=filename2)})
        insights.append(f"Linhas ({y_axis}): {df[y_axis].describe().to_dict()}")

        # 3) Gráfico de Dispersão
        chart_scatter = px.scatter(
            df,
            x=x_axis,
            y=y_axis,
            title=f"Dispersão: {x_axis} vs {y_axis}",
            color_discrete_sequence=[color]
        )
        chart_scatter.update_layout(
            template=selected_template,
            yaxis_tickformat=".0f"
        )
        chart3_html = pio.to_html(chart_scatter, full_html=False)
        filename3 = unique_chart_filename("chart_scatter")
        with open(os.path.join(CHARTS_DIR, filename3), "w", encoding="utf-8") as f:
            f.write(chart3_html)
        charts.append({"html": chart3_html, "url": url_for('download_chart', filename=filename3)})
        insights.append(f"Dispersão ({y_axis}): {df[y_axis].describe().to_dict()}")

        # 4) Gráfico de Área
        chart_area = px.area(
            df,
            x=x_axis,
            y=y_axis,
            title=f"Área: {x_axis} vs {y_axis}",
            color_discrete_sequence=[color]
        )
        chart_area.update_layout(
            template=selected_template,
            yaxis_tickformat=".0f"
        )
        chart4_html = pio.to_html(chart_area, full_html=False)
        filename4 = unique_chart_filename("chart_area")
        with open(os.path.join(CHARTS_DIR, filename4), "w", encoding="utf-8") as f:
            f.write(chart4_html)
        charts.append({"html": chart4_html, "url": url_for('download_chart', filename=filename4)})
        insights.append(f"Área ({y_axis}): {df[y_axis].describe().to_dict()}")

        # 5) Histograma
        chart_hist = px.histogram(
            df,
            x=y_axis,
            title=f"Histograma: {y_axis}",
            color_discrete_sequence=[color]
        )
        chart_hist.update_layout(
            template=selected_template,
            yaxis_tickformat=".0f"
        )
        chart5_html = pio.to_html(chart_hist, full_html=False)
        filename5 = unique_chart_filename("chart_histogram")
        with open(os.path.join(CHARTS_DIR, filename5), "w", encoding="utf-8") as f:
            f.write(chart5_html)
        charts.append({"html": chart5_html, "url": url_for('download_chart', filename=filename5)})
        insights.append(f"Histograma ({y_axis}): {df[y_axis].describe().to_dict()}")

        # 6) Gráfico 3D (se houver outra coluna numérica para z)
        other_numeric = [c for c in numeric_cols if c != y_axis]
        if len(other_numeric) >= 1:
            z_axis = other_numeric[0]
            chart_3d = px.scatter_3d(
                df,
                x=x_axis,
                y=y_axis,
                z=z_axis,
                title=f"3D: {x_axis}, {y_axis}, {z_axis}",
                color_discrete_sequence=[color]
            )
            chart_3d.update_layout(
                template=selected_template,
                scene=dict(
                    yaxis=dict(tickformat=".0f"),
                    xaxis=dict(tickformat=".0f"),
                    zaxis=dict(tickformat=".0f")
                )
            )
            chart6_html = pio.to_html(chart_3d, full_html=False)
            filename6 = unique_chart_filename("chart_3d")
            with open(os.path.join(CHARTS_DIR, filename6), "w", encoding="utf-8") as f:
                f.write(chart6_html)
            charts.append({"html": chart6_html, "url": url_for('download_chart', filename=filename6)})
            insights.append(f"3D ({y_axis}, {z_axis}): {df[z_axis].describe().to_dict()}")
        else:
            charts.append({
                "html": "<p style='color:#E0E0E0; text-align:center;'>Não há colunas numéricas suficientes para 3D.</p>",
                "url": None
            })
            insights.append(f"3D não disponível para {y_axis} (não há coluna z).")

    # Renderizar state=3
    return render_template(
        'index.html',
        state=3,
        columns=columns_list,
        numeric_cols=numeric_cols,
        unique_values=unique_values,
        data_uid=data_uid,
        background_color=background_color,
        selected_template=selected_template,
        x_axis=x_axis,
        y_axes=y_axes_valid,
        filter_column1=filter_column1,
        filter_value1=filter_value1,
        filter_column2=filter_column2,
        filter_value2=filter_value2,
        charts=charts,
        insights=insights,
        data_csv_url=data_csv_url,
        data_xlsx_url=data_xlsx_url
    )


@app.route('/download/<path:filename>')
def download_chart(filename):
    try:
        return send_from_directory(CHARTS_DIR, filename, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao baixar o gráfico: {e}", "danger")
        return redirect(url_for('dashboard'))


@app.route('/download_data/<path:filename>')
def download_data(filename):
    try:
        return send_from_directory(DATA_DIR, filename, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao baixar os dados: {e}", "danger")
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
