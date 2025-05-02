from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, SelectField, RadioField, TextAreaField, validators
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///etec.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Coordenador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14))
    banco = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    conta = db.Column(db.String(20))
    tipo_chave = db.Column(db.String(20))
    chave_pix = db.Column(db.String(100))
    unidade = db.Column(db.String(150))
    endereco = db.Column(db.String(200))
    centro_distribuicao = db.Column(db.String(10))
    coordenador_prova = db.Column(db.String(10))
    divulgacao = db.Column(db.String(100))
    outros_meios = db.Column(db.String(200))
    observacoes = db.Column(db.String(300))

class CadastroForm(Form):
    nome = StringField('Nome completo', [validators.InputRequired()])
    telefone = StringField('Telefone', [validators.Regexp(r'\d{10,11}')])
    cpf = StringField('CPF', [validators.Regexp(r'\d{11}')])
    banco = StringField('Banco', [validators.InputRequired()])
    agencia = StringField('Agência', [validators.InputRequired()])
    conta = StringField('Conta com dígito', [validators.InputRequired()])
    tipo_chave = SelectField('Tipo de chave Pix', choices=[('cpf', 'CPF'), ('telefone', 'Telefone'), ('email', 'E-mail'), ('aleatoria', 'Aleatória')])
    chave_pix = StringField('Chave Pix', [validators.InputRequired()])
    unidade = StringField('Nome da Unidade', [validators.InputRequired()])
    endereco = StringField('Endereço completo', [validators.InputRequired()])
    centro_distribuicao = RadioField('Centro de Distribuição?', choices=[('sim', 'Sim'), ('nao', 'Não')])
    coordenador_prova = RadioField('Coordenador de Local?', choices=[('sim', 'Sim'), ('nao', 'Não')])
    divulgacao = SelectField('Melhor meio de divulgação', choices=[('trafego', 'Tráfego Pago'), ('tv', 'TV'), ('panfletos', 'Panfletos'), ('banners', 'Banners'), ('outdoor', 'Outdoor'), ('outros', 'Outros')])
    outros_meios = StringField('Se outros, quais?')
    observacoes = TextAreaField('Observações e Sugestões')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CadastroForm(request.form)
    if request.method == 'POST' and form.validate():
        novo = Coordenador(
            nome=form.nome.data,
            telefone=form.telefone.data,
            cpf=form.cpf.data,
            banco=form.banco.data,
            agencia=form.agencia.data,
            conta=form.conta.data,
            tipo_chave=form.tipo_chave.data,
            chave_pix=form.chave_pix.data,
            unidade=form.unidade.data,
            endereco=form.endereco.data,
            centro_distribuicao=form.centro_distribuicao.data,
            coordenador_prova=form.coordenador_prova.data,
            divulgacao=form.divulgacao.data,
            outros_meios=form.outros_meios.data,
            observacoes=form.observacoes.data
        )
        db.session.add(novo)
        db.session.commit()
        return redirect('/')
    return render_template('form.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)    
