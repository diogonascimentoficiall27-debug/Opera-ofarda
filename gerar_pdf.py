# gerar_pdf.py — Motor PDF Operação Farda
# Geração de PDF de questões no padrão visual aprovado

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    HRFlowable, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from PIL import Image as PILImage

W, H = A4
MARGIN_L = 2.0 * cm
MARGIN_R = 2.0 * cm
MARGIN_T = 1.8 * cm
MARGIN_B = 1.8 * cm

LOGO_OF_PATH = os.path.join(os.path.dirname(__file__), 'static', 'logos', 'logo_of.png')

# ─────────────────────────────────────────────────────────────
# PRÉ-PROCESSAMENTO DE IMAGEM
# ─────────────────────────────────────────────────────────────

def preparar_brasao(path):
    """Recorta espaço em branco excessivo do brasão e retorna path limpo."""
    import numpy as np
    img = PILImage.open(path).convert('RGBA')
    arr = np.array(img)
    non_transparent = arr[:, :, 3] > 10
    if not non_transparent.any():
        return path
    rows = non_transparent.any(axis=1)
    cols = non_transparent.any(axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    pad = 15
    rmin = max(0, rmin - pad)
    rmax = min(arr.shape[0], rmax + pad)
    cmin = max(0, cmin - pad)
    cmax = min(arr.shape[1], cmax + pad)
    cropped = img.crop((cmin, rmin, cmax, rmax))
    out = path.replace('.png', '_clean.png').replace('.jpg', '_clean.png')
    cropped.save(out)
    return out


def preparar_logo_of(path):
    """Remove fundo preto da logo OF se necessário."""
    img = PILImage.open(path).convert('RGBA')
    # Já está limpa (salva recortada)
    return path


# ─────────────────────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────────────────────

def formatar_texto(texto):
    """
    Converte marcações simples em tags ReportLab XML:
    *palavra*  → <b>palavra</b>  (negrito)
    _palavra_  → <u>palavra</u>  (sublinhado)
    Escapa caracteres especiais XML antes de aplicar as tags.
    """
    if not texto:
        return texto
    import re
    # Escapar caracteres XML (exceto os que vamos inserir)
    texto = texto.replace('&', '&amp;')
    texto = texto.replace('<', '&lt;')
    texto = texto.replace('>', '&gt;')
    # Negrito: *palavra* → <b>palavra</b>
    texto = re.sub(r'\*([^*\n]+)\*', r'<b>\1</b>', texto)
    # Sublinhado: _palavra_ → <u>palavra</u>
    texto = re.sub(r'_([^_\n]+)_', r'<u>\1</u>', texto)
    return texto


def get_styles():
    return {
        'disciplina': ParagraphStyle(
            'Disciplina', fontName='Helvetica-Bold', fontSize=12,
            leading=16, textColor=colors.white, alignment=TA_CENTER
        ),
        'enunciado': ParagraphStyle(
            'Enunciado', fontName='Helvetica', fontSize=9.5,
            leading=14, textColor=colors.black,
            alignment=TA_JUSTIFY, spaceAfter=4
        ),
        'alternativa': ParagraphStyle(
            'Alternativa', fontName='Helvetica', fontSize=9.5,
            leading=13, textColor=colors.black,
            alignment=TA_JUSTIFY, spaceAfter=2
        ),
        'num_questao': ParagraphStyle(
            'NumQuestao', fontName='Helvetica-Bold', fontSize=10,
            leading=14, textColor=colors.black, spaceAfter=3
        ),
        'texto_apoio': ParagraphStyle(
            'TextoApoio', fontName='Helvetica-Oblique', fontSize=9,
            leading=13, textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY, leftIndent=10, rightIndent=10,
            spaceAfter=6, spaceBefore=4
        ),
        'atencao': ParagraphStyle(
            'Atencao', fontName='Helvetica-BoldOblique', fontSize=9,
            leading=13, textColor=colors.black,
            alignment=TA_LEFT, spaceAfter=4, spaceBefore=8
        ),
        'capa_titulo': ParagraphStyle(
            'CapaTitulo', fontName='Helvetica-Bold', fontSize=16,
            leading=22, alignment=TA_CENTER, spaceAfter=6
        ),
        'capa_sub': ParagraphStyle(
            'CapaSub', fontName='Helvetica', fontSize=13,
            leading=18, alignment=TA_CENTER, spaceAfter=4
        ),
        'capa_info': ParagraphStyle(
            'CapaInfo', fontName='Helvetica', fontSize=10.5,
            leading=15, alignment=TA_CENTER,
            textColor=colors.HexColor('#555555')
        ),
    }


# ─────────────────────────────────────────────────────────────
# COMPONENTES
# ─────────────────────────────────────────────────────────────

def make_disc_banner(texto, styles):
    t = Table(
        [[Paragraph(texto, styles['disciplina'])]],
        colWidths=[W - MARGIN_L - MARGIN_R]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return t


def header_footer(canvas, doc, brasao_path, concurso_nome):
    canvas.saveState()
    # Linha topo
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN_L, H - MARGIN_T + 0.2 * cm,
                W - MARGIN_R, H - MARGIN_T + 0.2 * cm)
    # Brasão
    if brasao_path and os.path.exists(brasao_path):
        canvas.drawImage(
            brasao_path,
            MARGIN_L, H - MARGIN_T - 0.9 * cm,
            width=1.3 * cm, height=1.3 * cm,
            preserveAspectRatio=True, mask='auto'
        )
    # Título header
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(
        MARGIN_L + 1.6 * cm,
        H - MARGIN_T - 0.35 * cm,
        f"OPERAÇÃO FARDA | QUESTÕES {concurso_nome.upper()}"
    )
    # Linha abaixo do header
    canvas.line(MARGIN_L, H - MARGIN_T - 1.1 * cm,
                W - MARGIN_R, H - MARGIN_T - 1.1 * cm)
    # Rodapé
    canvas.line(MARGIN_L, MARGIN_B - 0.2 * cm,
                W - MARGIN_R, MARGIN_B - 0.2 * cm)
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawString(MARGIN_L, MARGIN_B - 0.55 * cm, "Operação Farda\u2122")
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(
        MARGIN_L + 2.3 * cm, MARGIN_B - 0.55 * cm,
        "– Material gratuito. É proibida sua reprodução, distribuição ou comercialização total ou parcial, sem autorização."
    )
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(
        W - MARGIN_R, MARGIN_B - 0.55 * cm, f"Página {doc.page}"
    )
    canvas.restoreState()


def first_page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.drawString(MARGIN_L, MARGIN_B - 0.55 * cm, "Operação Farda\u2122")
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(
        MARGIN_L + 2.3 * cm, MARGIN_B - 0.55 * cm,
        "– Material gratuito. É proibida sua reprodução, distribuição ou comercialização total ou parcial, sem autorização."
    )
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────
# PARSER DE TEXTO CORRIDO
# ─────────────────────────────────────────────────────────────

def parse_texto_corrido(texto):
    """
    Interpreta texto corrido com suporte a múltiplas disciplinas e texto base.

    Formato aceito:
    [DISCIPLINA: Língua Portuguesa]

    [TEXTO BASE: Instrução para as questões de 1 a 5]
    Texto de apoio / trecho literário aqui...
    [/TEXTO BASE]

    1. Enunciado da questão...
    (A) alternativa A
    ...
    """
    import re

    questoes = []

    # Dividir o texto por marcadores de disciplina
    partes = re.split(r'\[DISCIPLINA\s*:\s*([^\]]+)\]', texto, flags=re.IGNORECASE)

    blocos = []  # lista de (disciplina, texto_bloco)
    if len(partes) == 1:
        blocos.append((None, partes[0]))
    else:
        if partes[0].strip():
            blocos.append((None, partes[0]))
        i = 1
        while i < len(partes) - 1:
            disc = partes[i].strip()
            conteudo = partes[i + 1]
            blocos.append((disc, conteudo))
            i += 2

    for disc, bloco_texto in blocos:

        # ── Extrair blocos de texto base ─────────────────────────
        # Formato: [TEXTO BASE: label] ... conteúdo ... [/TEXTO BASE]
        # Guarda lista de (posição_inicio_no_bloco, posição_fim, label, conteudo)
        textos_base = []
        padrao_tb = re.compile(
            r'\[TEXTO BASE\s*(?::\s*([^\]]*))?\](.*?)\[/TEXTO BASE\]',
            re.IGNORECASE | re.DOTALL
        )
        for m in padrao_tb.finditer(bloco_texto):
            label = (m.group(1) or '').strip()
            conteudo_tb = m.group(2).strip()
            textos_base.append({
                'start': m.start(),
                'end': m.end(),
                'label': label,
                'conteudo': conteudo_tb,
            })

        # Remover os blocos [TEXTO BASE] do texto para o parser de questões
        bloco_limpo = padrao_tb.sub('', bloco_texto)

        # ── Localizar questões ────────────────────────────────────
        padrao_questao = re.compile(r'^\s*(\d+)\s*[.)]\s+', re.MULTILINE)
        matches = list(padrao_questao.finditer(bloco_limpo))

        # Precisamos mapear posição das questões no texto original (com [TEXTO BASE])
        # para associar o texto base correto à questão seguinte.
        # Estratégia: reconstituir offsets no bloco_texto original por número de questão.
        # Mais simples: associar cada texto_base à questão imediatamente seguinte a ele.

        # Mapear cada questão (num) → posição no bloco_texto original
        questao_pos_orig = {}
        for m_orig in padrao_questao.finditer(bloco_texto):
            num = int(m_orig.group(1))
            if num not in questao_pos_orig:
                questao_pos_orig[num] = m_orig.start()

        # Para cada texto_base, encontrar a questão mais próxima após ele
        def questao_apos(tb_end):
            """Retorna o num da questão mais próxima após tb_end no bloco original."""
            candidatos = [(num, pos) for num, pos in questao_pos_orig.items() if pos > tb_end]
            if not candidatos:
                return None
            return min(candidatos, key=lambda x: x[1])[0]

        tb_por_questao = {}  # num_questao → {'label':..., 'conteudo':...}
        for tb in textos_base:
            num_q = questao_apos(tb['end'])
            if num_q is not None:
                # Se já existe um texto base para essa questão, concatena
                if num_q in tb_por_questao:
                    tb_por_questao[num_q]['conteudo'] += '\n\n' + tb['conteudo']
                else:
                    tb_por_questao[num_q] = {'label': tb['label'], 'conteudo': tb['conteudo']}

        # ── Parsear questões do bloco limpo ───────────────────────
        for idx, match in enumerate(matches):
            num = int(match.group(1))
            inicio = match.end()
            fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(bloco_limpo)
            conteudo_q = bloco_limpo[inicio:fim].strip()

            # Separar enunciado das alternativas
            alt_split = re.split(r'\n?\s*\(([AaBbCcDdEe])\)\s*', conteudo_q)
            enunciado = re.sub(r'\n{2,}', ' ', alt_split[0]).strip()

            alternativas = []
            j = 1
            while j < len(alt_split) - 1:
                letra = alt_split[j].upper()
                texto_alt = re.sub(r'\n+', ' ', alt_split[j + 1]).strip()
                if texto_alt:
                    alternativas.append((letra, texto_alt))
                j += 2

            if enunciado and alternativas:
                tb_info = tb_por_questao.get(num, {})
                questoes.append({
                    'num': num,
                    'enunciado': enunciado,
                    'alternativas': alternativas,
                    'texto_apoio': tb_info.get('conteudo') or None,
                    'label_apoio': tb_info.get('label') or None,
                    'disciplina': disc,
                })

    return questoes


# ─────────────────────────────────────────────────────────────
# GERADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────

def gerar_pdf(dados):
    """
    dados = {
        'concurso': 'PMBA Soldado 2026',
        'banca': 'FCC',
        'disciplina': 'Língua Portuguesa',
        'brasao_path': '/path/to/brasao.png',
        'questoes': [
            {
                'num': 1,
                'enunciado': '...',
                'alternativas': [('A','...'), ('B','...'),...],
                'texto_apoio': '...' ou None,
                'label_apoio': '...' ou None,
                'disciplina': '...' ou None  # para banner de nova disciplina
            },
            ...
        ]
    }
    Retorna bytes do PDF.
    """
    styles = get_styles()

    concurso  = dados.get('concurso', 'PMBA Soldado')
    banca     = dados.get('banca', 'FCC')
    brasao_original = dados.get('brasao_path', '')
    questoes  = dados.get('questoes', [])

    # Detectar disciplinas presentes para exibir na capa
    disciplinas_unicas = []
    for q in questoes:
        d = (q.get('disciplina') or '').strip()
        if d and d not in disciplinas_unicas:
            disciplinas_unicas.append(d)
    disc_capa = ' + '.join(disciplinas_unicas) if disciplinas_unicas else 'Questões Objetivas'

    # Preparar brasão
    brasao_path = ''
    if brasao_original and os.path.exists(brasao_original):
        brasao_path = preparar_brasao(brasao_original)

    logo_of = LOGO_OF_PATH

    # Buffer de saída
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 1.4 * cm,
        bottomMargin=MARGIN_B + 0.6 * cm,
        title=f"Operação Farda | {concurso}",
        author="Operação Farda",
    )

    story = []

    # ── CAPA ──────────────────────────────────────────────────
    story.append(Spacer(1, 2.5 * cm))

    # Brasão na capa
    if brasao_path and os.path.exists(brasao_path):
        logo_capa = Image(brasao_path, width=3.2 * cm, height=3.2 * cm)
        logo_capa.hAlign = 'CENTER'
        story.append(logo_capa)

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("OPERAÇÃO FARDA", styles['capa_titulo']))
    story.append(Paragraph(f"QUESTÕES {concurso.upper()}", styles['capa_sub']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Simulado | {disc_capa}", styles['capa_info']))
    story.append(Paragraph(f"Banca {banca} | {len(questoes)} Questões Objetivas", styles['capa_info']))
    story.append(Spacer(1, 4.0 * cm))

    # Logo OF na capa
    area_util = W - MARGIN_L - MARGIN_R
    logo_w = area_util * 0.72

    if os.path.exists(logo_of):
        try:
            pil_img = PILImage.open(logo_of)
            orig_w, orig_h = pil_img.size
            logo_h = logo_w * (orig_h / orig_w)
        except Exception:
            logo_h = logo_w * (261 / 1078)
        logo_of_img = Image(logo_of, width=logo_w, height=logo_h)
        logo_of_img.hAlign = 'CENTER'
        story.append(logo_of_img)

    story.append(PageBreak())

    # ── QUESTÕES ──────────────────────────────────────────────
    disc_atual = None

    for q in questoes:
        bloco = []

        # Banner automático ao detectar mudança de disciplina
        disc_q = (q.get('disciplina') or '').strip().upper()
        if disc_q and disc_q != disc_atual:
            if disc_atual is not None:
                bloco.append(Spacer(1, 0.2 * cm))
            bloco.append(make_disc_banner(disc_q, styles))
            bloco.append(Spacer(1, 0.4 * cm))
            disc_atual = disc_q
        
        # Texto de apoio
        if q.get('label_apoio'):
            bloco.append(Paragraph(formatar_texto(q['label_apoio']), styles['atencao']))
        if q.get('texto_apoio'):
            for linha in q['texto_apoio'].split('\n'):
                if linha.strip():
                    bloco.append(Paragraph(formatar_texto(linha.strip()), styles['texto_apoio']))
            bloco.append(Spacer(1, 0.2 * cm))
        
        # Número da questão
        bloco.append(Paragraph(f"<b>Questão {q['num']}</b>", styles['num_questao']))
        
        # Enunciado
        bloco.append(Paragraph(formatar_texto(q['enunciado']), styles['enunciado']))
        
        # Alternativas
        for letra, texto in q['alternativas']:
            bloco.append(Paragraph(f"({letra})  {formatar_texto(texto)}", styles['alternativa']))
        
        bloco.append(Spacer(1, 0.15 * cm))
        bloco.append(HRFlowable(
            width="100%", thickness=0.4,
            color=colors.HexColor('#cccccc')
        ))
        bloco.append(Spacer(1, 0.25 * cm))
        
        story.append(KeepTogether(bloco))
    
    # ── BUILD ─────────────────────────────────────────────────
    def _first(canvas, doc):
        first_page_footer(canvas, doc)
    
    def _later(canvas, doc):
        header_footer(canvas, doc, brasao_path, concurso)
    
    doc.build(story, onFirstPage=_first, onLaterPages=_later)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
