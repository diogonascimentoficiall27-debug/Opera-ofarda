# perfis_agendamento.py — Perfis de concurso e agendamento interno
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PERFIS_FILE = os.path.join(DATA_DIR, 'perfis.json')
AGENDA_FILE = os.path.join(DATA_DIR, 'agenda.json')


def _garantir_pasta():
    os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# PERFIS DE CONCURSO
# ─────────────────────────────────────────────────────────────

PERFIS_PADRAO = [
    {
        'id': 'pmba_soldado',
        'nome': 'PMBA Soldado',
        'concurso': 'PMBA Soldado 2026',
        'banca': 'FCC',
        'brasao': 'pmba.png',
        'cor': '#1565C0',
        'icone': '🛡️',
    },
    {
        'id': 'pmba_cfo',
        'nome': 'PMBA CFO',
        'concurso': 'CFO PMBA 2026',
        'banca': 'UNEB',
        'brasao': 'pmba.png',
        'cor': '#B71C1C',
        'icone': '⭐',
    },
    {
        'id': 'pmal_soldado',
        'nome': 'PM-AL Soldado',
        'concurso': 'PM-AL Soldado 2026',
        'banca': 'CEBRASPE / CESPE',
        'brasao': 'pmal.png',
        'cor': '#1B5E20',
        'icone': '🎯',
    },
]


def carregar_perfis():
    _garantir_pasta()
    if not os.path.exists(PERFIS_FILE):
        salvar_perfis(PERFIS_PADRAO)
        return PERFIS_PADRAO
    with open(PERFIS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def salvar_perfis(perfis):
    _garantir_pasta()
    with open(PERFIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(perfis, f, ensure_ascii=False, indent=2)


def criar_perfil(dados):
    perfis = carregar_perfis()
    novo_id = dados.get('nome', '').lower().replace(' ', '_').replace('-', '_')
    # Garantir ID único
    ids_existentes = [p['id'] for p in perfis]
    base_id = novo_id
    contador = 2
    while novo_id in ids_existentes:
        novo_id = f"{base_id}_{contador}"
        contador += 1

    perfil = {
        'id': novo_id,
        'nome': dados.get('nome', ''),
        'concurso': dados.get('concurso', ''),
        'banca': dados.get('banca', ''),
        'brasao': dados.get('brasao', ''),
        'cor': dados.get('cor', '#39FF14'),
        'icone': dados.get('icone', '🎯'),
    }
    perfis.append(perfil)
    salvar_perfis(perfis)
    return perfil


def atualizar_perfil(perfil_id, dados):
    perfis = carregar_perfis()
    for p in perfis:
        if p['id'] == perfil_id:
            for campo in ('nome', 'concurso', 'banca', 'brasao', 'cor', 'icone'):
                if campo in dados:
                    p[campo] = dados[campo]
    salvar_perfis(perfis)


def deletar_perfil(perfil_id):
    perfis = carregar_perfis()
    perfis = [p for p in perfis if p['id'] != perfil_id]
    salvar_perfis(perfis)


# ─────────────────────────────────────────────────────────────
# AGENDAMENTO
# ─────────────────────────────────────────────────────────────

DIAS_SEMANA = {
    'monday':    'Segunda',
    'tuesday':   'Terça',
    'wednesday': 'Quarta',
    'thursday':  'Quinta',
    'friday':    'Sexta',
    'saturday':  'Sábado',
    'sunday':    'Domingo',
}


def carregar_agenda():
    _garantir_pasta()
    if not os.path.exists(AGENDA_FILE):
        return []
    with open(AGENDA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def salvar_agenda(agenda):
    _garantir_pasta()
    with open(AGENDA_FILE, 'w', encoding='utf-8') as f:
        json.dump(agenda, f, ensure_ascii=False, indent=2)


def agendar_pdf(dados):
    """
    dados: {
        nome: str,
        concurso: str,
        disciplina: str,
        data: 'YYYY-MM-DD' ou dia da semana ('monday', etc),
        destino: 'grupo'|'pdf'|'plataforma',
        pdf_path: str (caminho do PDF já gerado),
        status: 'pendente'|'baixado'
    }
    """
    agenda = carregar_agenda()
    item = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'nome': dados.get('nome', ''),
        'concurso': dados.get('concurso', ''),
        'disciplina': dados.get('disciplina', ''),
        'data': dados.get('data', ''),
        'destino': dados.get('destino', 'pdf'),
        'pdf_path': dados.get('pdf_path', ''),
        'criado_em': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'status': 'pendente',
    }
    agenda.append(item)
    # Ordenar por data
    agenda.sort(key=lambda x: x.get('data', ''))
    salvar_agenda(agenda)
    return item


def marcar_baixado(item_id):
    agenda = carregar_agenda()
    for item in agenda:
        if item['id'] == item_id:
            item['status'] = 'baixado'
            item['baixado_em'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    salvar_agenda(agenda)


def deletar_agendamento(item_id):
    agenda = carregar_agenda()
    agenda = [i for i in agenda if i['id'] != item_id]
    salvar_agenda(agenda)


def agenda_da_semana():
    """Retorna os agendamentos organizados por dia da semana."""
    agenda = carregar_agenda()
    hoje = datetime.now().strftime('%Y-%m-%d')
    # Separar pendentes e baixados
    pendentes = [i for i in agenda if i['status'] == 'pendente']
    baixados  = [i for i in agenda if i['status'] == 'baixado']
    return {
        'pendentes': pendentes,
        'baixados': baixados,
        'total': len(agenda),
        'hoje': hoje,
    }
