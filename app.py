from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import os

# Definir o Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'

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
        color = request.form.get('color', '#636efa')
        background_color = request.form.get('background_color', '#121212')  # Recebe a cor de fundo
        template = request.form.get('template', 'plotly_dark')
        x_axis = request.form.get('x_axis')
        y_axis = request.form.get('y_axis')

        df = pd.read_csv(file)

        # Seleciona colunas padrão se o usuário não selecionar
        if not x_axis:
            x_axis = df.columns[0]  # primeira coluna
        if not y_axis:
            y_axis = df.select_dtypes(include=['float64', 'int64']).columns[0]  # primeira coluna numérica

        # Gerar múltiplos gráficos
        charts = []

        # Gráfico 1: Colunas/Barras
        chart_bar = px.bar(df, x=x_axis, y=y_axis, title="Gráfico de Colunas/Barras", color_discrete_sequence=[color])
        chart_bar.update_layout(template=template)
        charts.append(pio.to_html(chart_bar, full_html=False))

        # Gráfico 2: Linhas
        chart_line = px.line(df, x=x_axis, y=y_axis, title="Gráfico de Linhas", color_discrete_sequence=[color])
        chart_line.update_layout(template=template)
        charts.append(pio.to_html(chart_line, full_html=False))

        # Gráfico 3: Dispersão
        chart_scatter = px.scatter(df, x=x_axis, y=y_axis, title="Gráfico de Dispersão", color_discrete_sequence=[color])
        chart_scatter.update_layout(template=template)
        charts.append(pio.to_html(chart_scatter, full_html=False))

        # Gráfico 4: Área
        chart_area = px.area(df, x=x_axis, y=y_axis, title="Gráfico de Área", color_discrete_sequence=[color])
        chart_area.update_layout(template=template)
        charts.append(pio.to_html(chart_area, full_html=False))

        # Gráfico 5: Box Plot
        chart_box = px.box(df, x=x_axis, y=y_axis, title="Box Plot", color_discrete_sequence=[color])
        chart_box.update_layout(template=template)
        charts.append(pio.to_html(chart_box, full_html=False))

        # Gráfico 6: Heatmap
        chart_heatmap = px.density_heatmap(df, x=x_axis, y=y_axis, title="Gráfico de Calor", color_continuous_scale='Viridis')
        chart_heatmap.update_layout(template=template)
        charts.append(pio.to_html(chart_heatmap, full_html=False))

        # Gráfico 7: Circular (Sunburst)
        chart_circular = px.sunburst(df, path=[x_axis], values=y_axis, title="Gráfico Circular", color_discrete_sequence=[color])
        chart_circular.update_layout(template=template)
        charts.append(pio.to_html(chart_circular, full_html=False))

        # Renderiza os gráficos e a cor de fundo selecionada
        return render_template('index.html',
                               chart1_html=charts[0] if len(charts) > 0 else None,
                               chart2_html=charts[1] if len(charts) > 1 else None,
                               chart3_html=charts[2] if len(charts) > 2 else None,
                               chart4_html=charts[3] if len(charts) > 3 else None,
                               chart5_html=charts[4] if len(charts) > 4 else None,
                               chart6_html=charts[5] if len(charts) > 5 else None,
                               chart7_html=charts[6] if len(charts) > 6 else None,
                               columns=list(df.columns),
                               background_color=background_color)  # Passa a cor de fundo para o template

    except Exception as e:
        flash(f"Ocorreu um erro ao gerar o dashboard: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/download/<chart_id>/<file_format>')
def download(chart_id, file_format):
    try:
        if file_format == 'html':
            file_path = os.path.join("static", f"chart_{chart_id[-1]}.html")
        elif file_format == 'jpg':
            file_path = os.path.join("static", f"chart_{chart_id[-1]}.jpg")
        else:
            flash(f"Formato de arquivo não suportado: {file_format}", "danger")
            return redirect(url_for('index'))

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao baixar o arquivo: {e}", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
