# firebase_db.py — Integração Firebase Firestore | Operação Farda

import os
import json
from datetime import datetime

_db = None

def _get_db():
    global _db
    if _db is not None:
        return _db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            # 1) Variável de ambiente (produção Render)
            cred_json = os.environ.get('FIREBASE_CREDENTIALS', '')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                # 2) Credenciais embutidas (fallback local)
                cred_dict = {
                    "type": "service_account",
                    "project_id": "operacao-farda",
                    "private_key_id": "70674451b672051d05fe9aac8762768fa5b805ce",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3CyiqOGp6J7K0\nJ6qpGSuEOzTumuISi5IsnZQ3fghtzGzZQ2GM3Tv5EQ3BpxwdcyaZWaVK7A/fFNTR\nx3uSEHhJIijjxVcjAGQOs2imu0lOFt+2niiE3ug7XPGvcIY78sdfPCXPlFXhguDc\nqqWoMu2zR3Uy+cs3ExI2QFaY3rV/pT5N5I1le1sb15otUEp0PaX1eL+IEsCpWKQX\nXM59tV75xOgzeLN3hOvU/StOPSaLqVq9vakffa7vu3HynjIx0CXAlJY362fCE9Mp\niobhUJckvtir7jx3vG7VyKaTBcRPuKvyZiEFdbBNZNQf6CX5uXa9Yu3rqBMHhmqR\nlOoclRqbAgMBAAECggEAEb7FsvbkL7KAiyGbVGhpxRh+UbF3QEgCpEukjlqsE4Tx\neoCjSOY7xbInDMKYIazDrbM4qJJJGZ3p4ep+atMo7iIfJ7G+eFi12oz/FMbsXOMv\nzgL4N6VqizLABXuZr98h//QTUFP3nXS0OwBaLfu9+pbvYEFCN7UkG1lSa+CPZO/k\niMLYRKkajZbMl4oygE4DKCe5iAQPHLhK6bX5TpCNVhbgU2o8pf3oJyIxF45bSb8c\n61yQd3/mrKKdGEQl/nYBJqcss0Bq1UQHTdYdg867g6Pl6/yRegAeywmMtzAYdb2q\nPrREgpba9Aac+R/W5sRXN549iqHZ8GrSdyf3vsozNQKBgQDp6gc5A07C6bkidFa7\nbmheREUa172DH+PNgw7Vz5Lfolxuz69lTZ1Jzd9Vk9E/gnZ3OQbeUzCIccm82Nq9\ncUtKy6VPx6QieTp1yzwAkwpNEPKgTEcX6KEWVmTiqrunEzikM5MhFjS9sv7lnBel\nD/Nx4ROe0e2pyxr2Itrne+h/BQKBgQDIU4feFXEajiIq1JBP9uyccPWvibqXdYkU\neAYMUkXg4m3/aXHoZScwXD3B/rMbJoQIGvI7HIy5rg/wGBTgki6vSxFEm7WRkk7v\nqBstcXXXjOGIVtlt/WJZjxw3HWxRGYVenzGjh2eRCfx8UM+3gWz4/vvBaoojMkaN\nJytblWolHwKBgDQhskZklFMgX+Br6UCQlLYdpQEcf+IPY2fUA6RnRKaOuub/Zmm/\naISgW1vpO8NZwilEDmHSTIi8Q2fRNL7v1wXuaQNkzRHZzsud5duC6dLPKiPLnDSZ\n5fzieE2EG5pa0E7YJ7xCBLMah3CI30QsT+dbcFH/G2ayG2orznm0xdY5AoGBAK0+\neADbID5r7yaFP+y3yfadRgwyGzlC/3LBPdHIEQCkMaayJT1qxVJwY0RzJaf0TjjI\nPPZcAWPPIZ9s5Bk2ssMMM3nXA1ZKZpOiGSbauaPZBW6oVU9m03hKaIdNndAhNxMW\nr5IR1sI7FazZIlo7xucrdMPXhHFd2F/YIQoKFIrXAoGBAISHEUHbw7LackzgWpqY\nByfw7+i0n5aFwUuw0kMXfDOZJeWav9joxLLWl50k7Ens63w265dz9aJ6Meuk5NNI\nKKlQUlbIjgGSfq/ECDF2iihApCnnQOvNFKCfrB0AnbwN0qeGOuIvuWTe3V73RqY3\nRqlKltaZsSV4BCwgYwA4tp0c\n-----END PRIVATE KEY-----\n",
                    "client_email": "firebase-adminsdk-fbsvc@operacao-farda.iam.gserviceaccount.com",
                    "client_id": "105745616578844754331",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40operacao-farda.iam.gserviceaccount.com",
                    "universe_domain": "googleapis.com"
                }
                cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"[Firebase] Erro ao inicializar: {e}")
        return None


def firebase_disponivel():
    try:
        return _get_db() is not None
    except Exception:
        return False


# ─── PERFIS ───────────────────────────────────────────────────

def fb_carregar_perfis():
    db = _get_db()
    docs = db.collection('perfis').order_by('criado_em').stream()
    perfis = []
    for doc in docs:
        p = doc.to_dict()
        p['id'] = doc.id
        perfis.append(p)
    return perfis


def fb_criar_perfil(dados):
    db = _get_db()
    perfil = {
        'nome':      dados.get('nome', ''),
        'concurso':  dados.get('concurso', ''),
        'banca':     dados.get('banca', ''),
        'brasao':    dados.get('brasao', ''),
        'cor':       dados.get('cor', '#39FF14'),
        'icone':     dados.get('icone', '🎯'),
        'criado_em': datetime.now().isoformat(),
    }
    ref = db.collection('perfis').add(perfil)
    perfil['id'] = ref[1].id
    return perfil


def fb_atualizar_perfil(perfil_id, dados):
    db = _get_db()
    campos = {k: v for k, v in dados.items()
              if k in ('nome', 'concurso', 'banca', 'brasao', 'cor', 'icone')}
    db.collection('perfis').document(perfil_id).update(campos)


def fb_deletar_perfil(perfil_id):
    db = _get_db()
    db.collection('perfis').document(perfil_id).delete()


# ─── AGENDA ───────────────────────────────────────────────────

def fb_carregar_agenda():
    db = _get_db()
    docs = db.collection('agenda').order_by('data').stream()
    agenda = []
    for doc in docs:
        item = doc.to_dict()
        item['id'] = doc.id
        agenda.append(item)
    return agenda


def fb_agendar_pdf(dados):
    db = _get_db()
    item = {
        'nome':       dados.get('nome', ''),
        'concurso':   dados.get('concurso', ''),
        'disciplina': dados.get('disciplina', ''),
        'data':       dados.get('data', ''),
        'destino':    dados.get('destino', 'pdf'),
        'pdf_path':   dados.get('pdf_path', ''),
        'status':     'pendente',
        'criado_em':  datetime.now().strftime('%Y-%m-%d %H:%M'),
        'baixado_em': '',
    }
    ref = db.collection('agenda').add(item)
    item['id'] = ref[1].id
    return item


def fb_marcar_baixado(item_id):
    db = _get_db()
    db.collection('agenda').document(item_id).update({
        'status':     'baixado',
        'baixado_em': datetime.now().strftime('%Y-%m-%d %H:%M'),
    })


def fb_deletar_agendamento(item_id):
    db = _get_db()
    db.collection('agenda').document(item_id).delete()


def fb_agenda_da_semana():
    agenda = fb_carregar_agenda()
    return {
        'pendentes': [i for i in agenda if i.get('status') == 'pendente'],
        'baixados':  [i for i in agenda if i.get('status') == 'baixado'],
        'total':     len(agenda),
        'hoje':      datetime.now().strftime('%Y-%m-%d'),
    }


# ─── HISTÓRICO ────────────────────────────────────────────────

def fb_registrar_historico(dados):
    try:
        db = _get_db()
        item = {
            'concurso':       dados.get('concurso', ''),
            'disciplinas':    dados.get('disciplinas', ''),
            'banca':          dados.get('banca', ''),
            'destino':        dados.get('destino', 'pdf'),
            'total_questoes': dados.get('total_questoes', 0),
            'modo':           dados.get('modo', 'manual'),
            'gerado_em':      datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        db.collection('historico_pdfs').add(item)
    except Exception:
        pass


def fb_carregar_historico(limit=50):
    try:
        db = _get_db()
        docs = db.collection('historico_pdfs') \
                 .order_by('gerado_em', direction='DESCENDING') \
                 .limit(limit).stream()
        historico = []
        for doc in docs:
            h = doc.to_dict()
            h['id'] = doc.id
            historico.append(h)
        return historico
    except Exception:
        return []


def fb_dashboard():
    try:
        historico = fb_carregar_historico(limit=200)
        total = len(historico)
        por_destino = {}
        por_disciplina = {}
        for h in historico:
            d = h.get('destino', 'pdf')
            por_destino[d] = por_destino.get(d, 0) + 1
            for disc in h.get('disciplinas', '').split('_'):
                if disc:
                    por_disciplina[disc] = por_disciplina.get(disc, 0) + 1
        total_questoes = sum(h.get('total_questoes', 0) for h in historico)
        return {
            'total_pdfs':     total,
            'total_questoes': total_questoes,
            'por_destino':    por_destino,
            'por_disciplina': sorted(por_disciplina.items(), key=lambda x: -x[1])[:8],
            'recentes':       historico[:7],
        }
    except Exception:
        return {
            'total_pdfs': 0, 'total_questoes': 0,
            'por_destino': {}, 'por_disciplina': [], 'recentes': [],
        }
