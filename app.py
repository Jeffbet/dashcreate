from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

# Definir o Flask app
app = Flask(__name__, template_folder='.')
app.secret_key = 'supersecretkey'

# Diretório onde os arquivos serão salvos temporariamente
TEMP_DIR = 'static'

@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/dashboard')
def index():
    return render_template('index.html', columns=[])

@app.route('/generate_dashboard', methods=['POST'])
def generate_dashboard():
    try:
        file = request.files['file']
        if not file:
            flash("Nenhum arquivo foi enviado!", "danger")
            return redirect(url_for('index'))

        # Configurações dos gráficos
        color = request.form.get('color', '#636efa')
        background_color = request.form.get('background_color', '#121212')  # Cor de fundo
        template = request.form.get('template', 'plotly_dark')
        x_axis = request.form.get('x_axis')
        y_axis = request.form.get('y_axis')

        # Ler o arquivo CSV enviado
        df = pd.read_csv(file)

        # Seleciona colunas padrão se o usuário não selecionar
        if not x_axis or x_axis not in df.columns:
            x_axis = df.columns[0]  # Primeira coluna
        if not y_axis or y_axis not in df.columns:
            y_axis = df.select_dtypes(include=['float64', 'int64']).columns[0]  # Primeira coluna numérica

        # Gerar múltiplos gráficos
        charts = []
        chart_files = []
        insights = []

        # Função para salvar gráficos
        def save_chart(chart_html, chart_name):
            file_path = os.path.join(TEMP_DIR, f"{chart_name}.html")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(chart_html)
            return file_path

        # Função para gerar insights simples
        def generate_insight(df, x_axis, y_axis):
            if df[y_axis].dtype in ['float64', 'int64']:
                max_val = df[y_axis].max()
                min_val = df[y_axis].min()
                max_date = df[df[y_axis] == max_val][x_axis].values[0]
                min_date = df[df[y_axis] == min_val][x_axis].values[0]
                return f"O maior valor de {y_axis} foi {max_val} em {max_date}, e o menor valor foi {min_val} em {min_date}."
            return "Não há dados numéricos suficientes para gerar insights."

        # Gráfico 1: Colunas/Barras com Filtros
        chart_bar = px.bar(df, x=x_axis, y=y_axis, title="Gráfico de Colunas/Barras", color_discrete_sequence=[color])
        chart_bar.update_layout(template=template)
        chart_bar.update_traces(marker=dict(line=dict(color='rgb(8,48,107)', width=1.5)))
        chart_html = pio.to_html(chart_bar, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_1"))
        insights.append(generate_insight(df, x_axis, y_axis))

        # Gráfico 2: Linhas com Filtros
        chart_line = px.line(df, x=x_axis, y=y_axis, title="Gráfico de Linhas", color_discrete_sequence=[color])
        chart_line.update_layout(template=template)
        chart_line.update_traces(mode='lines+markers')
        chart_html = pio.to_html(chart_line, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_2"))
        insights.append(generate_insight(df, x_axis, y_axis))

        # Gráfico 3: Dispersão com Filtros
        chart_scatter = px.scatter(df, x=x_axis, y=y_axis, title="Gráfico de Dispersão", color_discrete_sequence=[color])
        chart_scatter.update_layout(template=template)
        chart_html = pio.to_html(chart_scatter, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_3"))
        insights.append(generate_insight(df, x_axis, y_axis))

        # Gráfico 4: Área com Filtros
        chart_area = px.area(df, x=x_axis, y=y_axis, title="Gráfico de Área", color_discrete_sequence=[color])
        chart_area.update_layout(template=template)
        chart_html = pio.to_html(chart_area, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_4"))
        insights.append(generate_insight(df, x_axis, y_axis))

        # Gráfico 5: Sunburst (Circular) com Filtros
        chart_sunburst = px.sunburst(df, path=[x_axis], values=y_axis, title="Gráfico Circular - Sunburst")
        chart_sunburst.update_layout(template=template)
        chart_html = pio.to_html(chart_sunburst, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_5"))
        insights.append("Gráfico Sunburst mostra a hierarquia de dados em um formato circular.")

        # Gráfico 6: Histograma com Filtros
        chart_histogram = px.histogram(df, x=x_axis, y=y_axis, title="Histograma", color_discrete_sequence=[color])
        chart_histogram.update_layout(template=template)
        chart_html = pio.to_html(chart_histogram, full_html=False)
        charts.append(chart_html)
        chart_files.append(save_chart(chart_html, "chart_6"))
        insights.append(generate_insight(df, x_axis, y_axis))

        # Gráfico 7: Gráfico 3D de Superfície com Filtros
        if len(df.select_dtypes(include=['float64', 'int64']).columns) >= 3:
            z_axis = df.select_dtypes(include=['float64', 'int64']).columns[2]
            chart_3d = px.scatter_3d(df, x=x_axis, y=y_axis, z=z_axis, title="Gráfico 3D de Superfície", color_discrete_sequence=[color])
            chart_3d.update_layout(template=template)
            chart_html = pio.to_html(chart_3d, full_html=False)
            charts.append(chart_html)
            chart_files.append(save_chart(chart_html, "chart_7"))
            insights.append("Gráfico 3D de superfície mostra a relação entre três variáveis numéricas.")
        else:
            charts.append("<p>Dados insuficientes para gerar o gráfico 3D.</p>")
            chart_files.append("")
            insights.append("Dados insuficientes para gerar o gráfico 3D.")

        # Renderiza os gráficos e a cor de fundo selecionada
        return render_template('index.html',
                               chart1_html=charts[0] if len(charts) > 0 else None,
                               chart2_html=charts[1] if len(charts) > 1 else None,
                               chart3_html=charts[2] if len(charts) > 2 else None,
                               chart4_html=charts[3] if len(charts) > 3 else None,
                               chart5_html=charts[4] if len(charts) > 4 else None,
                               chart6_html=charts[5] if len(charts) > 5 else None,
                               chart7_html=charts[6] if len(charts) > 6 else None,
                               chart_files=chart_files,
                               insights=insights,
                               columns=list(df.columns),
                               background_color=background_color)  # Passa a cor de fundo para o template

    except Exception as e:
        flash(f"Ocorreu um erro ao gerar o dashboard: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    try:
        # Caminho do arquivo no diretório estático
        file_path = os.path.join(TEMP_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash(f"Arquivo não encontrado: {filename}", "danger")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erro ao baixar o arquivo: {e}", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Certifique-se de que o diretório estático exista
    os.makedirs(TEMP_DIR, exist_ok=True)
    app.run(debug=True)
