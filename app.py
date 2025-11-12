import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
import PyPDF2
from io import BytesIO
import re

# Configuração da página
st.set_page_config(
    page_title="Agente Inteligente SARESP",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .metric-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    .filter-badge {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        display: inline-block;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'focus' not in st.session_state:
    st.session_state.focus = "Equipe Gestora"
if 'gemini_model' not in st.session_state:
    st.session_state.gemini_model = None
if 'last_filters' not in st.session_state:
    st.session_state.last_filters = None

def init_gemini():
    """Inicializa o modelo Gemini com o modelo correto"""
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
        if not api_key:
            st.error("⚠️ Configure GOOGLE_API_KEY nas secrets")
            st.stop()
        
        genai.configure(api_key=api_key)
               
        model = genai.GenerativeModel('gemini-2.5-pro')
        st.session_state.gemini_model = model
        return model
    except Exception as e:
        st.error(f"Erro ao configurar Gemini: {e}")
        st.stop()

def normalize_column_names(df):
    """Normaliza nomes de colunas para padrão consistente"""
    column_mapping = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Mapeamento para colunas padrão
        if 'código' in col_lower and 'escola' in col_lower or 'codesc' in col_lower:
            column_mapping[col] = 'codigo_escola'
        elif 'nome' in col_lower and 'escola' in col_lower or 'nomesc' in col_lower:
            column_mapping[col] = 'nome_escola'
        elif col_lower in ['serie_ano', 'série_ano', 'serie', 'ano']:
            column_mapping[col] = 'serie_ano'
        elif col_lower == 'turma':
            column_mapping[col] = 'turma'
        elif col_lower == 'sexo':
            column_mapping[col] = 'sexo'
    
    if column_mapping:
        df = df.rename(columns=column_mapping)
    
    return df

def load_data_file(file):
    """Carrega arquivo e retorna DataFrame com colunas normalizadas"""
    try:
        ext = file.name.split('.')[-1].lower()
        
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        elif ext == 'csv':
            df = pd.read_csv(file)
        elif ext == 'pdf':
            pdf = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in pdf.pages])
            return None, text
        else:
            return None, None
        
        # Normaliza nomes de colunas
        df = normalize_column_names(df)
        
        return df, None
    except Exception as e:
        st.error(f"Erro ao carregar {file.name}: {e}")
        return None, None

def analyze_dataframe(df, filename, filters_info=None):
    """Analisa DataFrame e retorna resumo estruturado"""
    
    if df.empty:
        return {
            'filename': filename,
            'total_alunos': 0,
            'colunas': [],
            'tipo': 'Nenhum dado encontrado',
            'filters_applied': filters_info
        }

    analysis = {
        'filename': filename,
        'total_alunos': len(df),
        'total_colunas': len(df.columns),
        'colunas': list(df.columns),
        'filters_applied': filters_info
    }
    
    # Identifica tipo de dados
    if 'profic_lp' in df.columns:
        analysis['tipo'] = 'EFAI - Anos Iniciais'
        analysis['disciplinas'] = ['Língua Portuguesa', 'Matemática']
    elif 'nota_ch' in df.columns:
        analysis['tipo'] = 'EFAF - Anos Finais'
        analysis['disciplinas'] = ['LP', 'Inglês', 'Ciências', 'Matemática', 'História', 'Geografia']
    elif 'nota_fil' in df.columns:
        analysis['tipo'] = 'EM - Ensino Médio'
        analysis['disciplinas'] = ['LP', 'Inglês', 'Biologia', 'Física', 'Química', 'Matemática', 'Geografia', 'História', 'Filosofia']
    else:
        analysis['tipo'] = 'Genérico'
        analysis['disciplinas'] = []
    
    # Estatísticas de notas principais
    if 'nota_lp' in df.columns and pd.api.types.is_numeric_dtype(df['nota_lp']):
        analysis['media_lp'] = round(df['nota_lp'].mean(), 2)
        analysis['min_lp'] = round(df['nota_lp'].min(), 2)
        analysis['max_lp'] = round(df['nota_lp'].max(), 2)
    
    if 'nota_mat' in df.columns and pd.api.types.is_numeric_dtype(df['nota_mat']):
        analysis['media_mat'] = round(df['nota_mat'].mean(), 2)
        analysis['min_mat'] = round(df['nota_mat'].min(), 2)
        analysis['max_mat'] = round(df['nota_mat'].max(), 2)
    
    # Estatísticas de todas as métricas numéricas
    numeric_cols = [col for col in df.columns if 
                    (col.startswith('nota_') or 
                     col.startswith('profic_') or 
                     col.startswith('porc_') or
                     col.startswith('acertos_')) and 
                    pd.api.types.is_numeric_dtype(df[col])]
    
    analysis['numeric_stats'] = {}
    for col in numeric_cols:
        analysis['numeric_stats'][col] = {
            'media': round(df[col].mean(), 2),
            'min': round(df[col].min(), 2),
            'max': round(df[col].max(), 2),
            'mediana': round(df[col].median(), 2)
        }
    
    # Distribuições de níveis
    level_cols = [col for col in df.columns if 
                  col.startswith('nivel_profic_') or 
                  col.startswith('nivSaeb_') or
                  col.startswith('classific_')]
    
    analysis['level_distributions'] = {}
    for col in level_cols:
        if col in df.columns:
            distribution = df[col].value_counts(normalize=True) * 100
            analysis['level_distributions'][col] = distribution.round(2).to_dict()
    
    # Informações de agrupamento
    if 'serie_ano' in df.columns:
        analysis['series'] = df['serie_ano'].value_counts().to_dict()
    
    if 'sexo' in df.columns:
        analysis['genero'] = df['sexo'].value_counts().to_dict()
    
    if 'turma' in df.columns:
        analysis['turmas'] = df['turma'].value_counts().to_dict()
    
    if 'nome_escola' in df.columns:
        analysis['num_escolas'] = df['nome_escola'].nunique()
        analysis['nomes_escolas'] = df['nome_escola'].unique().tolist()[:10]  # Limita a 10
    
    if 'codigo_escola' in df.columns:
        analysis['num_cod_escolas'] = df['codigo_escola'].nunique()
        analysis['cods_escolas'] = df['codigo_escola'].unique().tolist()[:10]  # Limita a 10
    
    return analysis

def extract_filters_from_prompt(prompt):
    """Extrai filtros do prompt do usuário de forma inteligente"""
    filters = {
        'codigo_escola': None,
        'nome_escola': None,
        'turma': None,
        'serie_ano': None,
        'sexo': None
    }
    
    prompt_lower = prompt.lower()
    
    # 1. CÓDIGO DA ESCOLA
    # Padrões: "código 5174", "escola 5174", "código da escola 5174", "cod 5174"
    patterns_codigo = [
        r'(?:c[oó]digo\s+(?:da\s+)?escola|escola|cod\.?)\s+(\d{4,6})',
        r'(?:escola\s+de\s+c[oó]digo|com\s+c[oó]digo)\s+(\d{4,6})'
    ]
    
    for pattern in patterns_codigo:
        match = re.search(pattern, prompt_lower)
        if match:
            filters['codigo_escola'] = int(match.group(1))
            break
    
    # 2. NOME DA ESCOLA (mais complexo)
    # Padrões: "da escola [NOME]", "escola [NOME]"
    patterns_nome = [
        r'(?:da\s+escola|escola)\s+([A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕa-záéíóúâêîôûãõ\s\.]{5,})',
        r'(?:na\s+escola|para\s+a\s+escola)\s+([A-ZÁÉÍÓÚÂÊÎÔÛÃÕ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕa-záéíóúâêîôûãõ\s\.]{5,})'
    ]
    
    for pattern in patterns_nome:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match and not filters['codigo_escola']:  # Só usa nome se não achou código
            filters['nome_escola'] = match.group(1).strip()
            break
    
    # 3. TURMA
    # Padrões: "turma A", "turma 6A", "da turma B"
    match = re.search(r'(?:turma|da\s+turma)\s+([A-Z0-9]{1,3})', prompt, re.IGNORECASE)
    if match:
        filters['turma'] = match.group(1).upper()
    
    # 4. SÉRIE/ANO
    # Padrões: "6º ano", "série 6", "do 7º", "ano 5"
    patterns_serie = [
        r'(\d+)[ºª°]?\s*(?:ano|série)',
        r'(?:ano|série)\s+(\d+)',
        r'do\s+(\d+)[ºª°]'
    ]
    
    for pattern in patterns_serie:
        match = re.search(pattern, prompt_lower)
        if match:
            filters['serie_ano'] = match.group(1)
            break
    
    # 5. SEXO/GÊNERO
    if any(word in prompt_lower for word in ['feminino', 'femininas', 'meninas', 'alunas']):
        filters['sexo'] = 'F'
    elif any(word in prompt_lower for word in ['masculino', 'masculinos', 'meninos', 'alunos']):
        filters['sexo'] = 'M'
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    return filters

def apply_filters_to_dataframe(df, filters):
    """Aplica filtros ao DataFrame"""
    filtered_df = df.copy()
    filters_applied = []
    
    for key, value in filters.items():
        if key == 'codigo_escola' and 'codigo_escola' in filtered_df.columns:
            if value in filtered_df['codigo_escola'].values:
                filtered_df = filtered_df[filtered_df['codigo_escola'] == value]
                filters_applied.append(f"Código da escola: {value}")
        
        elif key == 'nome_escola' and 'nome_escola' in filtered_df.columns:
            # Busca parcial case-insensitive
            mask = filtered_df['nome_escola'].str.contains(value, case=False, na=False)
            if mask.any():
                filtered_df = filtered_df[mask]
                escola_encontrada = filtered_df['nome_escola'].iloc[0]
                filters_applied.append(f"Escola: {escola_encontrada}")
        
        elif key == 'turma' and 'turma' in filtered_df.columns:
            if value in filtered_df['turma'].values:
                filtered_df = filtered_df[filtered_df['turma'] == value]
                filters_applied.append(f"Turma: {value}")
        
        elif key == 'serie_ano' and 'serie_ano' in filtered_df.columns:
            # Tenta converter série para diferentes formatos
            serie_str = str(value)
            mask = (filtered_df['serie_ano'].astype(str).str.contains(serie_str, na=False))
            if mask.any():
                filtered_df = filtered_df[mask]
                filters_applied.append(f"Série/Ano: {value}")
        
        elif key == 'sexo' and 'sexo' in filtered_df.columns:
            if value in filtered_df['sexo'].values:
                filtered_df = filtered_df[filtered_df['sexo'] == value]
                genero_text = "Feminino" if value == 'F' else "Masculino"
                filters_applied.append(f"Gênero: {genero_text}")
    
    if filters_applied and not filtered_df.empty:
        return filtered_df, filters_applied
    else:
        return None, None

def create_data_context(filtered_df_info=None):
    """Cria contexto consolidado de dados para o Gemini"""
    
    context = ""
    data_source = {}
    
    if filtered_df_info:
        # Modo filtrado
        df = filtered_df_info['df']
        filename = filtered_df_info['filename']
        filters = filtered_df_info.get('filters', [])
        
        if df.empty:
            return f"=== DADOS FILTRADOS ===\n\nNenhum dado encontrado para os filtros: {', '.join(filters)}\n"
        
        analysis = analyze_dataframe(df, filename, filters)
        context = f"=== ANÁLISE FOCADA (FILTROS APLICADOS) ===\n\n"
        context += f"🎯 FILTROS ATIVOS: {', '.join(filters)}\n\n"
        data_source[filename] = {'df': df, 'analysis': analysis}
    
    else:
        # Modo geral
        if not st.session_state.dataframes:
            return "Nenhum dado foi carregado ainda."
        
        context = "=== VISÃO GERAL DE TODOS OS DADOS ===\n\n"
        data_source = st.session_state.dataframes
    
    # Gera contexto detalhado
    for filename, info in data_source.items():
        df = info['df']
        analysis = info['analysis']
        
        if analysis['total_alunos'] == 0:
            context += f"📄 {filename}: Nenhum aluno encontrado\n\n"
            continue
        
        context += f"📄 ARQUIVO: {filename}\n"
        context += f"Tipo: {analysis['tipo']}\n"
        context += f"Total de alunos: {analysis['total_alunos']}\n\n"
        
        # Estatísticas principais
        if 'media_lp' in analysis:
            context += f"📊 LÍNGUA PORTUGUESA:\n"
            context += f"  - Média: {analysis['media_lp']}\n"
            context += f"  - Mínimo: {analysis['min_lp']}\n"
            context += f"  - Máximo: {analysis['max_lp']}\n\n"
        
        if 'media_mat' in analysis:
            context += f"📊 MATEMÁTICA:\n"
            context += f"  - Média: {analysis['media_mat']}\n"
            context += f"  - Mínimo: {analysis['min_mat']}\n"
            context += f"  - Máximo: {analysis['max_mat']}\n\n"
        
        # Outras métricas
        if 'numeric_stats' in analysis and analysis['numeric_stats']:
            outras_metricas = [k for k in analysis['numeric_stats'].keys() 
                              if k not in ['nota_lp', 'nota_mat']]
            if outras_metricas:
                context += f"📊 OUTRAS DISCIPLINAS/MÉTRICAS:\n"
                for col in outras_metricas[:5]:  # Limita a 5
                    stats = analysis['numeric_stats'][col]
                    context += f"  - {col}: média={stats['media']}, min={stats['min']}, max={stats['max']}\n"
                context += "\n"
        
        # Distribuições de níveis
        if 'level_distributions' in analysis and analysis['level_distributions']:
            context += f"📈 DISTRIBUIÇÃO DE NÍVEIS (% de alunos):\n"
            for col, dist in analysis['level_distributions'].items():
                context += f"  {col}:\n"
                for nivel, percent in sorted(dist.items(), key=lambda x: -x[1])[:3]:
                    context += f"    - {nivel}: {percent}%\n"
            context += "\n"
        
        # Informações de agrupamento
        if 'series' in analysis:
            series_info = [f"{k} ({v} alunos)" for k, v in list(analysis['series'].items())[:5]]
            context += f"📚 Séries/Anos: {', '.join(series_info)}\n"
        
        if 'turmas' in analysis:
            turmas_info = [f"{k} ({v} alunos)" for k, v in list(analysis['turmas'].items())[:5]]
            context += f"🏫 Turmas: {', '.join(turmas_info)}\n"
        
        if 'num_escolas' in analysis and analysis['num_escolas'] > 1:
            context += f"🏢 Total de escolas: {analysis['num_escolas']}\n"
            if 'nomes_escolas' in analysis:
                context += f"   Exemplos: {', '.join(analysis['nomes_escolas'][:3])}\n"
        
        # Amostra dos dados
        context += f"\n📋 AMOSTRA DOS DADOS (3 primeiras linhas):\n"
        sample = df.head(3).to_string(max_cols=10)
        context += sample + "\n"
        
        context += "\n" + "="*70 + "\n\n"
    
    return context

def get_focus_instructions(focus_type):
    """Retorna instruções específicas para cada foco"""
    instructions = {
        "Equipe Gestora": """
VOCÊ É UM ESPECIALISTA EM GESTÃO EDUCACIONAL. 
Analise os dados sob perspectiva estratégica:
- Identifique padrões e tendências nos resultados REAIS dos dados
- Use NÚMEROS ESPECÍFICOS dos dados fornecidos
- Foque em métricas agregadas (por escola, turma, disciplina)
- Proponha planos de ação com metas SMART
- Sugira intervenções sistêmicas
- Inclua indicadores de acompanhamento
- Seja específico, acionável e baseado em DADOS
""",
        "Professores": """
VOCÊ É UM PROFESSOR ESPECIALISTA EM METODOLOGIAS ATIVAS.
Crie conteúdo prático e engajador:
- Analise as DIFICULDADES ESPECÍFICAS identificadas nos dados
- Desenvolva planos de aula de 50 minutos
- Use metodologias lúdicas e gamificadas
- Inclua: objetivos claros, materiais, desenvolvimento passo a passo, avaliação
- Use jogos, desafios, trabalho em grupo
- Relacione com cotidiano dos alunos
- Seja CRIATIVO, DIVERTIDO e baseado nas necessidades REAIS dos alunos
- Utilize as técnicas de Doug Lemov e Princípios de Rosenshine
""",
        "Professores Especialistas": """
VOCÊ É UM FORMADOR DE PROFESSORES.
Desenvolva conteúdo de formação continuada:
- Analise as DEFASAGENS ESPECÍFICAS identificadas nos dados
- Apresente boas práticas pedagógicas baseadas em evidências
- Sugira atividades "mão na massa" para os professores aplicarem
- Inclua exemplos práticos e estudos de caso
- Proponha oficinas e workshops estruturados
- Forneça materiais de apoio concretos
- Foque em habilidades BNCC que estão em defasagem
- Seja PRÁTICO e focado em APLICAÇÃO IMEDIATA
"""}
    
    return instructions.get(focus_type, instructions["Equipe Gestora"])

def chat_with_agent(user_message):
    """Processa mensagem do usuário e retorna resposta do agente"""
    try:
        model = st.session_state.gemini_model
        if not model:
            return "Erro: Modelo Gemini não inicializado"
        
        # Verifica se há dados carregados
        if not st.session_state.dataframes:
            return "⚠️ Por favor, carregue os dados SARESP primeiro na barra lateral."
        
        # Extrai filtros do prompt
        filters = extract_filters_from_prompt(user_message)
        
        # Tenta aplicar filtros em todos os DataFrames
        filtered_data = None
        filters_applied = []
        
        if filters:
            for filename, info in st.session_state.dataframes.items():
                df = info['df']
                filtered_df, applied = apply_filters_to_dataframe(df, filters)
                
                if filtered_df is not None and not filtered_df.empty:
                    filtered_data = {
                        'df': filtered_df,
                        'filename': filename,
                        'filters': applied
                    }
                    filters_applied = applied
                    break  # Usa o primeiro DataFrame que teve filtros aplicados com sucesso
        
        # Cria contexto
        if filtered_data:
            data_context = create_data_context(filtered_df_info=filtered_data)
            st.session_state.last_filters = filters_applied
        else:
            data_context = create_data_context()
            st.session_state.last_filters = None
        
        focus_instructions = get_focus_instructions(st.session_state.focus)
        
        # Histórico recente
        history_context = ""
        if len(st.session_state.messages) > 0:
            history_context = "\n=== HISTÓRICO RECENTE ===\n"
            for msg in st.session_state.messages[-4:]:
                role = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
                history_context += f"{role}: {msg['content'][:200]}...\n"
        
        # Monta prompt completo
        full_prompt = f"""
{focus_instructions}

{data_context}

{history_context}

=== FOCO SELECIONADO ===
{st.session_state.focus}

=== PERGUNTA DO USUÁRIO ===
{user_message}

=== INSTRUÇÕES CRÍTICAS ===
1. Analise CUIDADOSAMENTE os dados fornecidos acima
2. Use NÚMEROS e ESTATÍSTICAS REAIS dos dados
3. Se filtros foram aplicados, foque APENAS nos dados filtrados
4. Seja ESPECÍFICO e PRÁTICO
5. Formate bem a resposta com títulos e seções claras usando markdown
6. Use bullet points quando apropriado
7. Se pedirem visualização, descreva qual tipo seria útil
8. Se pedirem plano de aula: estruture em 4 momentos de 50 minutos total
9. Se pedirem plano de ação: inclua diagnóstico, objetivos SMART, ações, cronograma
10. Se pedirem formação: inclua módulos, oficinas práticas, boas práticas

RESPONDA AGORA DE FORMA COMPLETA E ESTRUTURADA:
"""
        
        # Chama o Gemini
        response = model.generate_content(full_prompt)
        
        return response.text
        
    except Exception as e:
        return f"❌ Erro ao processar: {str(e)}\n\nTente novamente ou reformule sua pergunta."

def create_chart_from_request(prompt, filtered_df=None):
    """Cria visualização baseada em solicitação"""
    try:
        # Decide qual DataFrame usar
        if filtered_df is not None and not filtered_df.empty:
            df = filtered_df
            title_prefix = "DADOS FILTRADOS"
        elif st.session_state.dataframes:
            # Usa o primeiro dataframe disponível
            df = list(st.session_state.dataframes.values())[0]['df']
            title_prefix = "VISÃO GERAL"
        else:
            return None
        
        prompt_lower = prompt.lower()
        
        # 1. Distribuição de notas
        if any(word in prompt_lower for word in ['distribuição', 'histograma']):
            if 'nota_lp' in df.columns and 'nota_mat' in df.columns:
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df['nota_lp'].dropna(), 
                    name='Língua Portuguesa', 
                    opacity=0.7,
                    nbinsx=20
                ))
                fig.add_trace(go.Histogram(
                    x=df['nota_mat'].dropna(), 
                    name='Matemática', 
                    opacity=0.7,
                    nbinsx=20
                ))
                fig.update_layout(
                    title=f'{title_prefix} - Distribuição de Notas',
                    xaxis_title='Nota',
                    yaxis_title='Frequência',
                    barmode='overlay',
                    template='plotly_white',
                    height=450
                )
                return fig
        
        # 2. Comparação por gênero
        if any(word in prompt_lower for word in ['gênero', 'genero', 'sexo', 'feminino', 'masculino']):
            if 'sexo' in df.columns and 'nota_lp' in df.columns:
                dados_genero = df.groupby('sexo')[['nota_lp', 'nota_mat']].mean().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Língua Portuguesa',
                    x=['Feminino' if x=='F' else 'Masculino' for x in dados_genero['sexo']],
                    y=dados_genero['nota_lp']
                ))
                fig.add_trace(go.Bar(
                    name='Matemática',
                    x=['Feminino' if x=='F' else 'Masculino' for x in dados_genero['sexo']],
                    y=dados_genero['nota_mat']
                ))
                fig.update_layout(
                    title=f'{title_prefix} - Média de Notas por Gênero',
                    yaxis_title='Média',
                    barmode='group',
                    template='plotly_white',
                    height=450
                )
                return fig
        
        # 3. Boxplot por disciplina
        if 'boxplot' in prompt_lower or 'dispersão' in prompt_lower:
            notas_cols = [col for col in df.columns if col.startswith('nota_') and 'original' not in col]
            if len(notas_cols) > 1:
                fig = go.Figure()
                for col in notas_cols[:6]:
                    disciplina = col.replace('nota_', '').upper()
                    fig.add_trace(go.Box(y=df[col].dropna(), name=disciplina))
                fig.update_layout(
                    title=f'{title_prefix} - Distribuição de Notas por Disciplina (Boxplot)',
                    yaxis_title='Nota',
                    template='plotly_white',
                    height=450
                )
                return fig
        
        # 4. Gráfico de pizza para níveis
        if 'pizza' in prompt_lower or 'nível' in prompt_lower or 'nivel' in prompt_lower:
            nivel_cols = [col for col in df.columns if 'nivel' in col.lower() or 'classific' in col.lower()]
            if nivel_cols:
                col = nivel_cols[0]
                distribution = df[col].value_counts()
                fig = px.pie(
                    values=distribution.values,
                    names=distribution.index,
                    title=f'{title_prefix} - Distribuição de Níveis ({col})'
                )
                fig.update_layout(height=450)
                return fig
        
        # 5. Comparação por turma
        if 'turma' in prompt_lower:
            if 'turma' in df.columns and 'nota_lp' in df.columns:
                dados_turma = df.groupby('turma')[['nota_lp', 'nota_mat']].mean().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Bar(name='LP', x=dados_turma['turma'], y=dados_turma['nota_lp']))
                fig.add_trace(go.Bar(name='MAT', x=dados_turma['turma'], y=dados_turma['nota_mat']))
                fig.update_layout(
                    title=f'{title_prefix} - Média por Turma',
                    yaxis_title='Média',
                    xaxis_title='Turma',
                    barmode='group',
                    template='plotly_white',
                    height=450
                )
                return fig
        
        # 6. Comparação por série
        if 'série' in prompt_lower or 'serie' in prompt_lower:
            if 'serie_ano' in df.columns and 'nota_lp' in df.columns:
                dados_serie = df.groupby('serie_ano')[['nota_lp', 'nota_mat']].mean().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Bar(name='LP', x=dados_serie['serie_ano'], y=dados_serie['nota_lp']))
                fig.add_trace(go.Bar(name='MAT', x=dados_serie['serie_ano'], y=dados_serie['nota_mat']))
                fig.update_layout(
                    title=f'{title_prefix} - Média por Série/Ano',
                    yaxis_title='Média',
                    xaxis_title='Série/Ano',
                    barmode='group',
                    template='plotly_white',
                    height=450
                )
                return fig
        
        # Fallback: boxplot geral
        numeric_cols = [col for col in df.columns if col.startswith('nota_') and 'original' not in col]
        if numeric_cols:
            fig = go.Figure()
            for col in numeric_cols[:6]:
                fig.add_trace(go.Box(y=df[col].dropna(), name=col.replace('nota_', '')))
            fig.update_layout(
                title=f'{title_prefix} - Distribuição de Métricas',
                yaxis_title='Valor',
                template='plotly_white',
                height=450
            )
            return fig
        
        return None
        
    except Exception as e:
        st.error(f"Erro ao criar visualização: {e}")
        return None

def main():
    st.title("🎓 Agente Inteligente SARESP")
    st.markdown("*Análise Educacional com Google Gemini 2.5 Pro*")
    
    # Inicializa Gemini
    if not st.session_state.gemini_model:
        with st.spinner("Inicializando Google Gemini..."):
            init_gemini()
    
    # === SIDEBAR ===
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3976/3976625.png", width=80)
        st.title("⚙️ Configuração")
        
        # Seletor de foco
        st.markdown("### 🎯 Selecione o Foco")
        focus = st.selectbox(
            "Público-alvo",
            ["Equipe Gestora", "Professores", "Professores Especialistas"],
            label_visibility="collapsed"
        )
        st.session_state.focus = focus
        
        # Descrição do foco
        focus_desc = {
            "Equipe Gestora": "📊 Planos de ação, análises estratégicas e indicadores",
            "Professores": "👨‍🏫 Planos de aula lúdicos e gamificados (50 min)",
            "Professores Especialistas": "🎓 Formações, oficinas e boas práticas"
        }
        st.info(focus_desc[focus])
        
        st.markdown("---")
        
        # Upload de arquivos
        st.markdown("### 📤 Upload de Dados")
        uploaded_files = st.file_uploader(
            "Arquivos SARESP (CSV, XLSX, XLS)",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            with st.spinner("Processando arquivos..."):
                for file in uploaded_files:
                    if file.name not in st.session_state.dataframes:
                        df, text = load_data_file(file)
                        if df is not None:
                            analysis = analyze_dataframe(df, file.name)
                            st.session_state.dataframes[file.name] = {
                                'df': df,
                                'analysis': analysis
                            }
            
            # Mostra arquivos carregados
            st.success(f"✅ {len(st.session_state.dataframes)} arquivo(s) carregado(s)")
            
            for filename, info in st.session_state.dataframes.items():
                with st.expander(f"📄 {filename}"):
                    st.write(f"**Tipo:** {info['analysis']['tipo']}")
                    st.write(f"**Alunos:** {info['analysis']['total_alunos']}")
                    
                    if 'media_lp' in info['analysis']:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Média LP", info['analysis'].get('media_lp', 'N/A'))
                        with col2:
                            st.metric("Média MAT", info['analysis'].get('media_mat', 'N/A'))
                    
                    # Mostra escolas disponíveis
                    if 'num_escolas' in info['analysis']:
                        st.write(f"**Escolas:** {info['analysis']['num_escolas']}")
                        if info['analysis']['num_escolas'] <= 5:
                            st.write("**Códigos:**", ", ".join(map(str, info['analysis'].get('cods_escolas', []))))
        
        st.markdown("---")
        
        # Mostra filtros ativos
        if st.session_state.last_filters:
            st.markdown("### 🎯 Filtros Ativos")
            for filter_text in st.session_state.last_filters:
                st.markdown(f'<div class="filter-badge">{filter_text}</div>', unsafe_allow_html=True)
            st.markdown("---")
        
        if st.session_state.dataframes:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.dataframes = {}
                st.session_state.messages = []
                st.session_state.last_filters = None
                st.rerun()
        
        # Instruções
        with st.expander("ℹ️ Como usar"):
            st.markdown("""
**Passos:**
1. Faça upload dos arquivos SARESP
2. Selecione o foco desejado
3. Converse com o agente no chat

**Filtros Inteligentes:**
O agente detecta automaticamente:
- **"código 5174"** ou **"escola 5174"**
- **"turma A"** ou **"turma 6A"**
- **"6º ano"** ou **"série 5"**
- **"feminino"** ou **"masculino"**

**Exemplos:**
- "Analise a escola código 5174"
- "Qual média da turma 6A?"
- "Compare gêneros do 7º ano"
- "Plano de ação para código 901748"
- "Gráfico da escola 5162"
            """)
    
    # === ÁREA PRINCIPAL - CHAT ===
    
    # Mensagem de boas-vindas
    if not st.session_state.dataframes:
        st.info("👈 Comece fazendo upload dos arquivos SARESP na barra lateral")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 📊 Equipe Gestora")
            st.markdown("- Análise de resultados\n- Planos de ação\n- Indicadores e metas")
        with col2:
            st.markdown("### 👨‍🏫 Professores")
            st.markdown("- Planos de aula 50 min\n- Atividades lúdicas\n- Gamificação")
        with col3:
            st.markdown("### 🎓 Especialistas")
            st.markdown("- Formações\n- Oficinas práticas\n- Boas práticas")
        
        st.stop()
    
    # Mostra histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Se tem gráfico anexado, mostra
            if "chart" in message and message["chart"]:
                st.plotly_chart(message["chart"], use_container_width=True)
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta ou solicitação..."):
        # Adiciona mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Processa e responde
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analisando..."):
                response = chat_with_agent(prompt)
                st.markdown(response)
                
                # Verifica se deve criar visualização
                chart = None
                if any(word in prompt.lower() for word in ['gráfico', 'visualização', 'visualizar', 'mostrar', 'plotar', 'distribuição', 'comparação', 'boxplot', 'pizza']):
                    # Se há filtros aplicados, usa dados filtrados
                    filtered_df = None
                    if st.session_state.last_filters:
                        # Tenta obter DataFrame filtrado
                        filters = extract_filters_from_prompt(prompt)
                        if filters:
                            for filename, info in st.session_state.dataframes.items():
                                df = info['df']
                                filtered_df, _ = apply_filters_to_dataframe(df, filters)
                                if filtered_df is not None:
                                    break
                    
                    chart = create_chart_from_request(prompt, filtered_df)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                
                # Salva resposta
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "chart": chart
                })
    
    # Sugestões rápidas
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Sugestões de perguntas:")
        
        # Pega código de escola do primeiro arquivo se disponível
        exemplo_codigo = ""
        if st.session_state.dataframes:
            first_df = list(st.session_state.dataframes.values())[0]
            if 'cods_escolas' in first_df['analysis'] and first_df['analysis']['cods_escolas']:
                exemplo_codigo = str(first_df['analysis']['cods_escolas'][0])
        
        suggestions = {
            "Equipe Gestora": [
                f"Analise os resultados da escola código {exemplo_codigo}" if exemplo_codigo else "Analise os resultados gerais",
                "Quais turmas precisam de mais atenção?",
                "Crie um plano de ação para melhorar matemática no 6º ano",
                "Compare o desempenho entre as turmas"
            ],
            "Professores": [
                "Crie um plano de aula gamificado sobre frações para 5º ano",
                "Desenvolva atividades lúdicas para interpretação de texto",
                "Plano de aula de 50 minutos sobre sistema solar",
                "Como trabalhar operações matemáticas de forma divertida?"
            ],
            "Professores Especialistas": [
                "Desenvolva formação sobre metodologias ativas",
                "Crie oficina prática sobre avaliação formativa",
                "Quais estratégias para trabalhar habilidades em defasagem?",
                "Programa de formação sobre gamificação"
            ]
        }
        
        cols = st.columns(2)
        for idx, suggestion in enumerate(suggestions[focus][:4]):
            with cols[idx % 2]:
                if st.button(suggestion, key=f"sug_{focus}_{idx}", use_container_width=True):
                    # Simula entrada do usuário
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    with st.spinner("🤔 Analisando..."):
                        response = chat_with_agent(suggestion)
                        chart = None
                        if any(word in suggestion.lower() for word in ['gráfico', 'visualização', 'visualizar', 'mostrar', 'plotar', 'distribuição', 'comparação']):
                            chart = create_chart_from_request(suggestion)
                        st.session_state.messages.append({"role": "assistant", "content": response, "chart": chart})
                    st.rerun()

if __name__ == "__main__":
    main()