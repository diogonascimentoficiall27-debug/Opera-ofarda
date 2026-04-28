# app.py — Servidor Flask | Operação Farda PDF Generator
import os
import json
import io
import random
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename

# Carregar .env se existir (desenvolvimento local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from gerar_pdf import gerar_pdf, parse_texto_corrido
from ia_questoes import gerar_questoes_ia, limpar_formatacao, DESTINOS
from perfis_agendamento import (
    carregar_perfis, criar_perfil, atualizar_perfil, deletar_perfil,
    carregar_agenda, agendar_pdf, marcar_baixado, deletar_agendamento, agenda_da_semana
)
import firebase_db as fdb

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-troque-em-producao')

# ── CORS ──────────────────────────────────────────────────────
FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    if FRONTEND_URL == '*' or origin == FRONTEND_URL or not origin:
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 204

# ── CONFIG ────────────────────────────────────────────────────
BRASOES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'logos', 'brasoes')
PDFS_DIR    = os.path.join(os.path.dirname(__file__), 'pdfs_agendados')
ALLOWED_EXT = {'png', 'jpg', 'jpeg'}

DISCIPLINAS = [
    "Língua Portuguesa", "Matemática", "História do Brasil",
    "Geografia do Brasil", "Atualidades", "Informática",
    "Direito Constitucional", "Direito Administrativo",
    "Direito Penal", "Direito Penal Militar",
    "Direito Processual Penal", "Direito Processual Penal Militar",
    "Direitos Humanos", "Igualdade Racial e de Gênero",
    "Legislação Específica", "Conhecimentos Regionais",
    "Redação", "Outra",
]

BANCAS = [
    "FCC", "CEBRASPE / CESPE", "IBFC", "VUNESP",
    "IDECAN", "AOCP", "FAPEMS", "IADES", "QUADRIX", "Outra"
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def listar_brasoes():
    brasoes = []
    for f in sorted(os.listdir(BRASOES_DIR)):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) and '_clean' not in f:
            nome = os.path.splitext(f)[0].upper().replace('_', ' ')
            brasoes.append({'arquivo': f, 'nome': nome})
    return brasoes


def _usar_firebase():
    return fdb.firebase_disponivel()


# ─────────────────────────────────────────────────────────────
# ROTAS PRINCIPAIS
# ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    perfis = fdb.fb_carregar_perfis() if _usar_firebase() else carregar_perfis()
    agenda = fdb.fb_agenda_da_semana() if _usar_firebase() else agenda_da_semana()
    return render_template(
        'index.html',
        disciplinas=DISCIPLINAS,
        bancas=BANCAS,
        brasoes=listar_brasoes(),
        perfis=perfis,
        destinos=DESTINOS,
        agenda=agenda,
        supabase_ativo=_usar_firebase(),
    )


@app.route('/brasoes')
def get_brasoes():
    return jsonify(listar_brasoes())


@app.route('/upload-brasao', methods=['POST'])
def upload_brasao():
    if 'brasao' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    file = request.files['brasao']
    nome_pm = request.form.get('nome_pm', '').strip()
    if not nome_pm:
        return jsonify({'erro': 'Informe o nome da PM'}), 400
    if not allowed_file(file.filename):
        return jsonify({'erro': 'Formato inválido. Use PNG ou JPG'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(nome_pm.lower().replace(' ', '_')) + '.' + ext
    file.save(os.path.join(BRASOES_DIR, filename))
    return jsonify({'sucesso': True, 'arquivo': filename, 'nome': nome_pm.upper(), 'brasoes': listar_brasoes()})


# ─────────────────────────────────────────────────────────────
# PERFIS
# ─────────────────────────────────────────────────────────────

@app.route('/perfis', methods=['GET'])
def get_perfis():
    perfis = fdb.fb_carregar_perfis() if _usar_firebase() else carregar_perfis()
    return jsonify(perfis)


@app.route('/perfis', methods=['POST'])
def post_perfil():
    data = request.get_json()
    if not data or not data.get('nome'):
        return jsonify({'erro': 'Nome do perfil obrigatório'}), 400
    if _usar_firebase():
        perfil = fdb.fb_criar_perfil(data)
        perfis = fdb.fb_carregar_perfis()
    else:
        perfil = criar_perfil(data)
        perfis = carregar_perfis()
    return jsonify({'sucesso': True, 'perfil': perfil, 'perfis': perfis})


@app.route('/perfis/<perfil_id>', methods=['PATCH'])
def patch_perfil(perfil_id):
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400
    if _usar_firebase():
        fdb.fb_atualizar_perfil(perfil_id, data)
        perfis = fdb.fb_carregar_perfis()
    else:
        atualizar_perfil(perfil_id, data)
        perfis = carregar_perfis()
    return jsonify({'sucesso': True, 'perfis': perfis})


@app.route('/perfis/<perfil_id>', methods=['DELETE'])
def delete_perfil(perfil_id):
    if _usar_firebase():
        fdb.fb_deletar_perfil(perfil_id)
        perfis = fdb.fb_carregar_perfis()
    else:
        deletar_perfil(perfil_id)
        perfis = carregar_perfis()
    return jsonify({'sucesso': True, 'perfis': perfis})


# ─────────────────────────────────────────────────────────────
# AGENDA
# ─────────────────────────────────────────────────────────────

@app.route('/agenda', methods=['GET'])
def get_agenda():
    ag = fdb.fb_agenda_da_semana() if _usar_firebase() else agenda_da_semana()
    return jsonify(ag)


@app.route('/agenda/<item_id>/baixado', methods=['POST'])
def post_baixado(item_id):
    if _usar_firebase():
        fdb.fb_marcar_baixado(item_id)
        ag = fdb.fb_agenda_da_semana()
    else:
        marcar_baixado(item_id)
        ag = agenda_da_semana()
    return jsonify({'sucesso': True, 'agenda': ag})


@app.route('/agenda/<item_id>', methods=['DELETE'])
def delete_agenda(item_id):
    if _usar_firebase():
        fdb.fb_deletar_agendamento(item_id)
        ag = fdb.fb_agenda_da_semana()
    else:
        deletar_agendamento(item_id)
        ag = agenda_da_semana()
    return jsonify({'sucesso': True, 'agenda': ag})


@app.route('/agenda/<item_id>/download', methods=['GET'])
def download_agendado(item_id):
    if _usar_firebase():
        agenda_lista = fdb.fb_carregar_agenda()
    else:
        agenda_lista = carregar_agenda()
    item = next((i for i in agenda_lista if str(i['id']) == str(item_id)), None)
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404
    pdf_path = item.get('pdf_path', '')
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'erro': 'PDF não encontrado no servidor'}), 404
    if _usar_firebase():
        fdb.fb_marcar_baixado(item_id)
    else:
        marcar_baixado(item_id)
    return send_file(pdf_path, mimetype='application/pdf',
                     as_attachment=True, download_name=os.path.basename(pdf_path))


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@app.route('/dashboard')
def get_dashboard():
    if _usar_firebase():
        return jsonify(fdb.fb_dashboard())
    return jsonify({'total_pdfs': 0, 'total_questoes': 0,
                    'por_destino': {}, 'por_disciplina': [], 'recentes': []})


# ─────────────────────────────────────────────────────────────
# GERAR PDF
# ─────────────────────────────────────────────────────────────

@app.route('/gerar', methods=['POST'])
def gerar():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    concurso    = data.get('concurso', 'Concurso')
    banca       = data.get('banca', '')
    brasao_arq  = data.get('brasao', '')
    modo        = data.get('modo', 'manual')
    agendar     = data.get('agendar', False)
    data_agenda = data.get('data_agenda', '')
    nome_agenda = data.get('nome_agenda', '')
    destino     = data.get('destino', 'pdf')
    embaralhar  = data.get('embaralhar', False)

    brasao_path = ''
    if brasao_arq:
        brasao_path = os.path.join(BRASOES_DIR, brasao_arq)

    if modo == 'texto':
        texto_corrido = data.get('texto_corrido', '')
        if not texto_corrido.strip():
            return jsonify({'erro': 'Texto corrido vazio'}), 400
        questoes = parse_texto_corrido(texto_corrido)
        if not questoes:
            return jsonify({'erro': 'Não foi possível interpretar o texto. Verifique o formato.'}), 400
    else:
        questoes_raw = data.get('questoes', [])
        questoes = []
        for q in questoes_raw:
            enunciado = limpar_formatacao(q.get('enunciado', '').strip())
            if not enunciado:
                continue
            alts = []
            for letra in ['A', 'B', 'C', 'D', 'E']:
                txt = limpar_formatacao(q.get(f'alt_{letra}', '').strip())
                if txt:
                    alts.append((letra, txt))
            questoes.append({
                'num': q.get('num', len(questoes) + 1),
                'enunciado': enunciado,
                'alternativas': alts,
                'texto_apoio': limpar_formatacao(q.get('texto_apoio') or ''),
                'label_apoio': limpar_formatacao(q.get('label_apoio') or ''),
                'disciplina': q.get('disciplina') or None,
            })

    if not questoes:
        return jsonify({'erro': 'Nenhuma questão válida encontrada'}), 400

    # Embaralhar questões e alternativas
    if embaralhar:
        random.shuffle(questoes)
        for i, q in enumerate(questoes):
            q['num'] = i + 1
            alts = list(q['alternativas'])
            random.shuffle(alts)
            letras = ['A', 'B', 'C', 'D', 'E']
            q['alternativas'] = [(letras[j], alt[1]) for j, alt in enumerate(alts)]

    try:
        pdf_bytes = gerar_pdf({
            'concurso': concurso, 'banca': banca,
            'brasao_path': brasao_path, 'questoes': questoes,
        })
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar PDF: {str(e)}'}), 500

    discs = []
    for q in questoes:
        d = (q.get('disciplina') or '').strip()
        if d and d not in discs:
            discs.append(d)
    disc_str = '_'.join(d.replace(' ', '')[:8] for d in discs[:2]) or 'Questoes'
    nome_arquivo = f"OF_{concurso.replace(' ', '_')}_{disc_str}.pdf"

    # Registrar histórico
    if _usar_firebase():
        fdb.fb_registrar_historico({
            'concurso': concurso, 'disciplinas': disc_str,
            'banca': banca, 'destino': destino,
            'total_questoes': len(questoes), 'modo': modo,
        })

    # Agendamento
    if agendar and data_agenda:
        os.makedirs(PDFS_DIR, exist_ok=True)
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        pdf_path = os.path.join(PDFS_DIR, f"{ts}_{nome_arquivo}")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        dados_ag = {'nome': nome_agenda or nome_arquivo, 'concurso': concurso,
                    'disciplina': disc_str, 'data': data_agenda,
                    'destino': destino, 'pdf_path': pdf_path}
        if _usar_firebase():
            fdb.fb_agendar_pdf(dados_ag)
        else:
            agendar_pdf(dados_ag)
        return jsonify({'sucesso': True, 'agendado': True, 'nome': nome_agenda or nome_arquivo})

    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True, download_name=nome_arquivo)


@app.route('/parsear', methods=['POST'])
def parsear():
    data = request.get_json()
    texto = data.get('texto', '')
    questoes = parse_texto_corrido(texto)
    return jsonify({
        'total': len(questoes),
        'questoes': [
            {
                'num': q['num'],
                'enunciado': q['enunciado'][:80] + '...' if len(q['enunciado']) > 80 else q['enunciado'],
                'total_alts': len(q['alternativas']),
                'disciplina': q.get('disciplina', ''),
                'tem_texto_base': bool(q.get('texto_apoio')),
            }
            for q in questoes
        ]
    })


# ─────────────────────────────────────────────────────────────
# IA
# ─────────────────────────────────────────────────────────────

@app.route('/gerar-ia', methods=['POST'])
def gerar_ia():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados inválidos'}), 400

    api_key     = data.get('api_key', '').strip()
    provedor    = data.get('provedor', 'anthropic').strip()
    modelo      = data.get('modelo', '').strip()
    disciplina  = data.get('disciplina', '').strip()
    banca       = data.get('banca', 'FCC').strip()
    topico      = data.get('topico', '').strip()
    quantidade  = int(data.get('quantidade', 10))
    dificuldade = data.get('dificuldade', 'medio').strip()
    concurso    = data.get('concurso', 'Concurso').strip()
    destino     = data.get('destino', 'pdf').strip()

    if not api_key:
        return jsonify({'erro': 'Informe sua API Key'}), 400
    if not disciplina:
        return jsonify({'erro': 'Selecione uma disciplina'}), 400

    questoes, erro = gerar_questoes_ia(
        api_key=api_key, disciplina=disciplina, banca=banca,
        topico=topico, quantidade=quantidade, dificuldade=dificuldade,
        concurso=concurso, destino=destino, provedor=provedor, modelo=modelo,
    )

    if erro:
        return jsonify({'erro': erro}), 400

    return jsonify({'sucesso': True, 'questoes': [
        {
            'num': q['num'],
            'enunciado': q['enunciado'],
            'alternativas': [{'letra': l, 'texto': t} for l, t in q['alternativas']],
            'disciplina': q['disciplina'],
            'destino': q.get('destino', destino),
        }
        for q in questoes
    ]})


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  OPERAÇÃO FARDA — Gerador de Questões PDF")
    print(f"  Supabase: {'✅ Ativo' if _usar_firebase() else '⚠️  Usando arquivos locais'}")
    print("  Acesse: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=os.environ.get('FLASK_ENV') != 'production', port=5000)
