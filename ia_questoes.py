# ia_questoes.py — Geração de questões via API Anthropic
import json
import re

DESTINOS = {
    'grupo': {
        'label': '📱 Grupo WhatsApp',
        'descricao': 'Engajamento e treino diário — material de divulgação',
        'cor': '#4a9eff',
        'instrucoes': """DESTINO: Grupo WhatsApp (material de divulgação gratuita)
- Crie questões boas para treino e engajamento diário
- Pode se basear em padrões recorrentes de provas anteriores da banca
- Misture: 40% adaptadas de provas reais + 40% inspiradas na banca + 20% inéditas simples
- NÃO é necessário ineditismo absoluto — foco em clareza e aprendizado rápido""",
    },
    'pdf': {
        'label': '📄 PDF Público',
        'descricao': 'Material equilibrado para apostilas e PDFs de divulgação',
        'cor': '#f0a500',
        'instrucoes': """DESTINO: PDF público (apostila/material de divulgação)
- Crie questões equilibradas entre qualidade e acessibilidade
- Misture: 40% adaptadas de provas reais + 40% inspiradas na banca + 20% inéditas
- Questões bem elaboradas mas sem consumir o melhor material inédito
- Foco em cobertura ampla do conteúdo programático""",
    },
    'plataforma': {
        'label': '🏆 Plataforma Premium',
        'descricao': 'Questões inéditas exclusivas para banco de questões e simulados',
        'cor': '#39FF14',
        'instrucoes': """DESTINO: Plataforma premium (banco de questões / simulados exclusivos)
- Crie questões INÉDITAS e de alto valor técnico
- Distribuição: 70% completamente inéditas + 20% adaptadas de alto nível + 10% referências selecionadas
- Maior fidelidade ao edital e ao estilo refinado da banca
- Evite estruturas e padrões já muito recorrentes em provas públicas
- Foco em qualidade premium, profundidade conceitual e exclusividade
- Nível de elaboração superior ao material de divulgação""",
    },
}


def limpar_formatacao(texto):
    """Corrige formatação automática: espaços, travessões, aspas, quebras."""
    if not texto:
        return texto
    # Espaços duplos
    texto = re.sub(r' {2,}', ' ', texto)
    # Quebras de linha múltiplas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # Travessão longo → hífen simples
    texto = texto.replace('\u2014', '-').replace('\u2013', '-')
    # Aspas tipográficas → aspas simples
    texto = texto.replace('\u201c', '"').replace('\u201d', '"')
    texto = texto.replace('\u2018', "'").replace('\u2019', "'")
    # Espaço antes de pontuação
    texto = re.sub(r' ([.,;:!?])', r'\1', texto)
    # Espaço no início/fim
    texto = texto.strip()
    # Múltiplos espaços após pontuação
    texto = re.sub(r'([.,;:!?]) {2,}', r'\1 ', texto)
    return texto


def montar_prompt(disciplina, banca, topico, quantidade, dificuldade, concurso, destino='pdf'):
    nivel_desc = {
        'facil':  'nível básico, cobrando conceitos diretos e definições',
        'medio':  'nível intermediário, com interpretação e aplicação prática',
        'dificil': 'nível avançado, com pegadinhas, casos concretos e detalhes que a banca costuma explorar',
    }.get(dificuldade, 'nível intermediário')

    topico_str = f"com foco no tópico: {topico}" if topico else "abrangendo os principais tópicos do edital"
    instrucoes_destino = DESTINOS.get(destino, DESTINOS['pdf'])['instrucoes']

    return f"""Você é um especialista em elaboração de questões de concursos públicos brasileiros.

Gere exatamente {quantidade} questões objetivas de múltipla escolha para o concurso de {concurso}, disciplina de {disciplina}, no estilo da banca {banca}, {topico_str}.

Dificuldade: {nivel_desc}.

{instrucoes_destino}

REGRAS OBRIGATÓRIAS:
- Cada questão deve ter exatamente 5 alternativas: (A), (B), (C), (D) e (E)
- Apenas UMA alternativa correta por questão
- As alternativas incorretas devem ser plausíveis e conter os erros típicos que a banca {banca} costuma usar
- O enunciado deve ser claro, objetivo e sem ambiguidade
- NÃO inclua o gabarito na resposta
- NÃO numere as alternativas com números, apenas com letras (A) a (E)

FORMATO DE RESPOSTA — responda APENAS com o JSON abaixo, sem texto adicional, sem markdown:

{{
  "questoes": [
    {{
      "num": 1,
      "enunciado": "Texto completo do enunciado aqui...",
      "alternativas": [
        {{"letra": "A", "texto": "Texto da alternativa A"}},
        {{"letra": "B", "texto": "Texto da alternativa B"}},
        {{"letra": "C", "texto": "Texto da alternativa C"}},
        {{"letra": "D", "texto": "Texto da alternativa D"}},
        {{"letra": "E", "texto": "Texto da alternativa E"}}
      ]
    }}
  ]
}}"""


def _parsear_resposta_json(resposta_raw):
    """Limpa e parseia o JSON retornado pela IA."""
    resposta = resposta_raw.strip()
    resposta = re.sub(r'^```json\s*', '', resposta)
    resposta = re.sub(r'^```\s*', '', resposta)
    resposta = re.sub(r'\s*```$', '', resposta).strip()
    return json.loads(resposta)


def _montar_questoes(questoes_raw, disciplina, destino):
    questoes = []
    for q in questoes_raw:
        alternativas = [
            (alt['letra'], limpar_formatacao(alt['texto']))
            for alt in q.get('alternativas', [])
            if alt.get('letra') and alt.get('texto')
        ]
        if q.get('enunciado') and alternativas:
            questoes.append({
                'num': q.get('num', len(questoes) + 1),
                'enunciado': limpar_formatacao(q['enunciado']),
                'alternativas': alternativas,
                'disciplina': disciplina,
                'destino': destino,
                'texto_apoio': None,
                'label_apoio': None,
            })
    return questoes


def _chamar_anthropic(api_key, prompt):
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("Biblioteca 'anthropic' não instalada. Rode: pip install anthropic")
    client = anthropic.Anthropic(api_key=api_key.strip())
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def _chamar_openai(api_key, prompt):
    import urllib.request
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _chamar_gemini(api_key, prompt):
    import urllib.request
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _chamar_openrouter(api_key, prompt, modelo):
    import urllib.request
    modelo = modelo or "mistralai/mistral-7b-instruct"
    payload = json.dumps({
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://operacaofarda.com.br",
            "X-Title": "Operação Farda",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def gerar_questoes_ia(api_key, disciplina, banca, topico, quantidade, dificuldade, concurso,
                      destino='pdf', provedor='anthropic', modelo=''):
    if not api_key or not api_key.strip():
        return None, "Informe sua API Key."

    prompt = montar_prompt(disciplina, banca, topico, quantidade, dificuldade, concurso, destino)

    try:
        if provedor == 'anthropic':
            resposta_raw = _chamar_anthropic(api_key.strip(), prompt)
        elif provedor == 'openai':
            resposta_raw = _chamar_openai(api_key.strip(), prompt)
        elif provedor == 'gemini':
            resposta_raw = _chamar_gemini(api_key.strip(), prompt)
        elif provedor == 'openrouter':
            resposta_raw = _chamar_openrouter(api_key.strip(), prompt, modelo)
        else:
            return None, f"Provedor '{provedor}' não reconhecido."

        dados = _parsear_resposta_json(resposta_raw)
        questoes_raw = dados.get('questoes', [])
        if not questoes_raw:
            return None, "A IA não retornou questões. Tente novamente."

        questoes = _montar_questoes(questoes_raw, disciplina, destino)
        if not questoes:
            return None, "Não foi possível processar as questões geradas. Tente novamente."

        return questoes, None

    except json.JSONDecodeError:
        return None, "Erro ao processar resposta da IA. Tente novamente."
    except RuntimeError as e:
        return None, str(e)
    except Exception as e:
        msg = str(e)
        if 'AuthenticationError' in msg or '401' in msg or 'Unauthorized' in msg:
            return None, "API Key incorreta ou expirada. Verifique suas credenciais."
        if 'RateLimitError' in msg or '429' in msg:
            return None, "Limite de requisições atingido. Aguarde alguns segundos e tente novamente."
        if 'ConnectionError' in msg or 'URLError' in msg or 'timeout' in msg.lower():
            return None, "Sem conexão com a API. Verifique sua internet."
        return None, f"Erro inesperado: {msg}"
