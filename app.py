from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

# Definir o Flask app
app = Flask(__name__, template_folder='.')
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

        # Outros gráficos...
        # (Mantenha os mesmos códigos de geração de gráficos)

        # Renderiza os gráficos e a cor de fundo selecionada
        return render_template('index.html',
                               chart1_html=charts[0] if len(charts) > 0 else None,
                               # Outros gráficos...
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
        else:
            flash(f"Formato de arquivo não suportado: {file_format}", "danger")
            return redirect(url_for('index'))

        # Verifique se o arquivo existe antes de enviar
        if not os.path.exists(file_path):
            flash(f"Arquivo não encontrado: {file_path}", "danger")
            return redirect(url_for('index'))

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao baixar o arquivo: {e}", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
