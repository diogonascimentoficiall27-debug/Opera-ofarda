# Operação Farda — Gerador de Questões PDF

Sistema web para geração de PDFs de questões para concursos de Polícia Militar.

---

## Arquitetura de produção

```
Netlify  →  serve o frontend (HTML/CSS/JS estático — pasta /static + /templates)
    ↕  fetch API (CORS configurado)
Render   →  Flask backend (gerar PDF, IA, parsear questões)
    ↕  REST API
Supabase →  banco de dados (perfis, agenda, histórico de PDFs)
```

---

## 1. Configurar o Supabase

1. Acesse [supabase.com](https://supabase.com) e crie um projeto gratuito
2. Vá em **SQL Editor** e execute o seguinte script para criar as tabelas:

```sql
-- Tabela de perfis de concurso
create table perfis (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  concurso text default '',
  banca text default '',
  brasao text default '',
  cor text default '#39FF14',
  icone text default '🎯',
  criado_em timestamp default now()
);

-- Tabela de agenda de PDFs
create table agenda (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  concurso text default '',
  disciplina text default '',
  data text default '',
  destino text default 'pdf',
  pdf_path text default '',
  status text default 'pendente',
  criado_em text default '',
  baixado_em text default ''
);

-- Tabela de histórico de PDFs gerados
create table historico_pdfs (
  id uuid primary key default gen_random_uuid(),
  concurso text default '',
  disciplinas text default '',
  banca text default '',
  destino text default 'pdf',
  total_questoes integer default 0,
  modo text default 'manual',
  gerado_em text default ''
);

-- Habilitar acesso público (anon key)
alter table perfis enable row level security;
alter table agenda enable row level security;
alter table historico_pdfs enable row level security;

create policy "allow all" on perfis for all using (true) with check (true);
create policy "allow all" on agenda for all using (true) with check (true);
create policy "allow all" on historico_pdfs for all using (true) with check (true);
```

3. Vá em **Settings → API** e copie:
   - `Project URL` → será sua `SUPABASE_URL`
   - `anon public key` → será sua `SUPABASE_KEY`

---

## 2. Deploy do backend no Render.com

1. Suba o projeto para um repositório GitHub (sem o arquivo `.env`)
2. Acesse [render.com](https://render.com) e clique em **New → Web Service**
3. Conecte seu repositório GitHub
4. Render detecta o `render.yaml` automaticamente. Confirme as configurações:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120`
5. Em **Environment Variables**, adicione:
   | Variável | Valor |
   |---|---|
   | `SUPABASE_URL` | URL do seu projeto Supabase |
   | `SUPABASE_KEY` | anon key do Supabase |
   | `FRONTEND_URL` | URL do seu app Netlify (ex: `https://meu-app.netlify.app`) |
   | `FLASK_ENV` | `production` |
6. Clique em **Deploy**
7. Anote a URL gerada (ex: `https://operacao-farda-api.onrender.com`)

> **Importante:** O plano gratuito do Render hiberna após 15 min de inatividade. A primeira requisição pode demorar ~30 segundos para acordar o servidor.

---

## 3. Deploy do frontend na Netlify

1. Crie uma pasta separada `frontend/` com os arquivos estáticos gerados pelo Flask:
   - `static/css/style.css`
   - `static/js/main.js`
   - `static/logos/`
   - `index.html` (versão compilada com o Jinja resolvido, ou use um `netlify.toml` com redirect)

**Alternativa mais simples (recomendada):**

   Configure o `main.js` para apontar para a URL do Render em vez de `/`:

```js
// No topo do main.js, defina a URL da API:
const API_URL = 'https://operacao-farda-api.onrender.com';

// E substitua todos os fetch('/rota') por fetch(`${API_URL}/rota`)
```

2. Na Netlify, crie um novo site via **Add new site → Import an existing project**
3. Conecte ao GitHub (pasta `frontend/`)
4. Clique em **Deploy site**

---

## 4. Desenvolvimento local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/operacao-farda-app.git
cd operacao-farda-app

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o .env (copie o exemplo)
cp .env.example .env
# Edite o .env com suas credenciais Supabase

# 4. Inicie o servidor
python app.py
# Acesse: http://localhost:5000
```

Sem as variáveis do Supabase configuradas, o sistema usa os arquivos JSON locais automaticamente.

---

## Formatação de texto nas questões

| Marcação | Resultado no PDF |
|---|---|
| `*palavra*` | **negrito** |
| `_palavra_` | <u>sublinhado</u> |

Funciona no enunciado, alternativas e texto de apoio.

---

## Formato do Texto Corrido

```
[DISCIPLINA: Língua Portuguesa]

[TEXTO BASE: Atenção: Para responder às questões de 1 a 3, leia o texto abaixo.]
Texto base / trecho literário aqui...
Pode ter múltiplos parágrafos.
[/TEXTO BASE]

1. Enunciado da primeira questão aqui...

(A) Alternativa A
(B) Alternativa B
(C) Alternativa C
(D) Alternativa D
(E) Alternativa E

[DISCIPLINA: Direito Constitucional]

11. Próxima questão...
```

---

## Estrutura de pastas

```
operacao-farda-app/
├── app.py                  ← Servidor Flask
├── gerar_pdf.py            ← Motor PDF (ReportLab)
├── ia_questoes.py          ← Geração com IA (multi-provedor)
├── supabase_db.py          ← Integração Supabase
├── perfis_agendamento.py   ← Fallback local (sem Supabase)
├── requirements.txt
├── render.yaml             ← Config deploy Render.com
├── .env.example            ← Modelo de variáveis de ambiente
├── .gitignore
├── static/
│   ├── logos/
│   │   ├── logo_of.png
│   │   └── brasoes/        ← Brasões das PMs (PNG/JPG)
│   ├── css/style.css
│   └── js/main.js
└── templates/
    └── index.html
```

---

Gerado pela plataforma **Operação Farda™**
