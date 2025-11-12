---
license: mit
title: Agente Inteligente SARESP - Análise Educacional com IA
sdk: streamlit
emoji: 🚀
colorFrom: blue
colorTo: green
---
# 🎓 Agente Inteligente SARESP - Análise Educacional com Google Gemini

![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Pro-orange.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)

Aplicação **focada em chat** para análise de dados educacionais do SARESP usando **Google Gemini 2.5 Pro** e **Streamlit**.

## 🚀 Características Principais

### 💬 Chat como Interface Central
- **Todo funcionamento através do chat**
- Agente analisa dados reais dos arquivos SARESP
- Respostas contextualizadas baseadas no foco selecionado
- Histórico de conversação mantido

### 🎯 Três Focos Especializados

**1. Equipe Gestora** 📊
- Análises estratégicas dos resultados
- Planos de ação com metas SMART
- Indicadores e métricas educacionais
- Intervenções sistêmicas

**2. Professores** 👨‍🏫
- Planos de aula lúdicos e gamificados (50 minutos)
- Atividades baseadas nas dificuldades dos alunos
- Metodologias ativas e engajadoras
- Exercícios práticos

**3. Professores Especialistas** 🎓
- Programas de formação continuada
- Oficinas práticas "mão na massa"
- Boas práticas pedagógicas
- Estratégias para habilidades em defasagem

### 📊 Análise Inteligente de Dados
- Processa arquivos SARESP (CSV, XLSX, XLS)
- Identifica automaticamente tipo de dados (EFAI, EFAF, EM)
- Calcula estatísticas e métricas relevantes
- Cria contexto rico para o Gemini

### 📈 Visualizações sob Demanda
- Gráficos gerados quando solicitados no chat
- Distribuição de notas
- Comparações por gênero
- Boxplots por disciplina
- Integradas diretamente no chat

## 🛠️ Instalação

### ☁️ Deploy no Hugging Face Spaces (Recomendado)

1. **Criar Space**
   ```
   - Acesse: https://huggingface.co/spaces
   - Clique em "Create new Space"
   - Nome: agente-saresp (ou escolha outro)
   - SDK: Streamlit
   - Hardware: CPU basic (gratuito)
   ```

2. **Upload de Arquivos**
   - Faça upload de `app.py`
   - Faça upload de `requirements.txt`
   - Faça upload de `README.md` (opcional)

3. **Configurar API Key**
   ```
   - Obtenha chave em: https://makersuite.google.com/app/apikey
   - No Space: Settings → Repository secrets
   - Adicione: GOOGLE_API_KEY = sua-chave-aqui
   ```

4. **Pronto!** 🎉
   - Aguarde 2-3 minutos para o build
   - Sua aplicação estará online

### 💻 Instalação Local

```bash
# Clone ou baixe os arquivos
git clone seu-repositorio
cd agente-saresp

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure API Key
mkdir .streamlit
echo 'GOOGLE_API_KEY = "sua-api-key-aqui"' > .streamlit/secrets.toml

# Execute
streamlit run app.py
```

## 📖 Como Usar

### 1️⃣ Upload dos Dados
- Na sidebar, faça upload dos arquivos SARESP
- Formatos aceitos: CSV, XLSX, XLS
- Múltiplos arquivos suportados

### 2️⃣ Selecione o Foco
- Escolha o público-alvo:
  - Equipe Gestora
  - Professores
  - Professores Especialistas

### 3️⃣ Converse com o Agente
Digite suas perguntas no chat, por exemplo:

#### Para Equipe Gestora:
- *"Analise os resultados gerais da escola"*
- *"Quais turmas precisam de mais atenção?"*
- *"Crie um plano de ação para melhorar matemática no 6º ano"*
- *"Mostre gráfico de distribuição de notas"*

#### Para Professores:
- *"Crie um plano de aula gamificado sobre frações para o 5º ano"*
- *"Desenvolva atividades lúdicas para interpretação de texto"*
- *"Plano de aula de 50 minutos sobre sistema solar"*

#### Para Professores Especialistas:
- *"Desenvolva formação sobre metodologias ativas"*
- *"Crie oficina prática sobre avaliação formativa"*
- *"Programa de formação sobre gamificação"*

### 4️⃣ O Agente Responde
- Analisa os dados reais carregados
- Gera resposta personalizada pelo foco
- Cria visualizações se solicitado
- Mantém contexto da conversa

## 💡 Exemplos Práticos

### Exemplo 1: Análise Estratégica
```
👤 Usuário: "Analise os resultados gerais e identifique as 3 principais defasagens"

🤖 Agente: [Analisa os dados e retorna]:
"Com base nos 1.247 alunos analisados, identifiquei:

1. MATEMÁTICA - 6º Ano
   - Média: 3.8/10
   - 67% abaixo da média esperada
   - Tópico crítico: Frações e operações

2. CIÊNCIAS - 7º Ano
   - Média: 4.2/10
   - 58% em nível básico
   - Tópico crítico: Corpo humano

3. LÍNGUA PORTUGUESA - 9º Ano
   - Média: 5.1/10
   - 45% com dificuldade em interpretação
   - Tópico crítico: Texto argumentativo"
```

### Exemplo 2: Plano de Aula
```
👤 Usuário: "Crie um plano de aula gamificado sobre frações para o 5º ano"

🤖 Agente: [Gera plano completo estruturado com]:
- Identificação (disciplina, ano, habilidades BNCC)
- Objetivos de aprendizagem
- Materiais necessários
- 4 momentos de 50 minutos:
  * Motivação (10 min) - "Pizzaria da Turma"
  * Desenvolvimento (25 min) - "Batalha das Frações"
  * Consolidação (10 min) - "Arquiteto de Frações"
  * Avaliação (5 min) - Quiz Relâmpago
- Exercícios lúdicos detalhados
- Sistema de pontuação e gamificação
```

### Exemplo 3: Visualização
```
👤 Usuário: "Mostre gráfico comparando desempenho por gênero"

🤖 Agente: [Gera resposta + gráfico interativo Plotly]
```

## 🎨 Estrutura dos Dados SARESP

### EFAI - Ensino Fundamental Anos Iniciais
- Língua Portuguesa e Matemática
- Proficiência e classificação SAEB
- Níveis: Abaixo do Básico, Básico, Adequado, Avançado

### EFAF - Ensino Fundamental Anos Finais
- LP, Inglês, Ciências, Matemática, História, Geografia
- Notas, acertos e porcentagens

### EM - Ensino Médio
- LP, Inglês, Biologia, Física, Química, Matemática, Geografia, História, Filosofia
- Análise completa por área de conhecimento

## 🔧 Tecnologias

- **Streamlit 1.31.0** - Framework web
- **Google Gemini 1.5 Pro** - IA Generativa
- **Pandas 2.1.4** - Análise de dados
- **Plotly 5.18.0** - Visualizações interativas
- **OpenPyXL 3.1.2** - Processamento Excel

## 🎯 Diferencial

### Por que este agente é especial?

✅ **Focado em Chat** - Interface natural e intuitiva
✅ **Análise Real** - Usa dados reais dos arquivos, não inventa
✅ **Contextualizado** - Respostas específicas por foco
✅ **Prático** - Gera documentos completos e acionáveis
✅ **Visual** - Cria gráficos sob demanda
✅ **Educacional** - Desenvolvido especificamente para educação

## 📝 Limitações

- Requer API Key do Google (gratuita com limites)
- Processa até ~50MB por arquivo
- Histórico de chat não persiste entre sessões
- Visualizações limitadas a gráficos pré-definidos

## 🔐 Segurança

- API Key armazenada em secrets (nunca exposta)
- Dados processados em memória (não salvos em disco)
- Sem persistência de dados sensíveis
- Limpo automaticamente ao fechar sessão

## 🐛 Resolução de Problemas

### Erro: "Configure GOOGLE_API_KEY"
**Solução:** Adicione a chave nas secrets do HF ou arquivo local

### Gemini não responde
**Solução:** Verifique se arquivos foram carregados e processados

### Visualização não aparece
**Solução:** Use palavras-chave como "gráfico", "mostrar", "visualizar"

## 📞 Suporte

- 📖 Leia esta documentação
- 🐛 Reporte problemas no GitHub Issues
- 💬 Contato através do Hugging Face Space

## 🚀 Roadmap

- [ ] Suporte a mais formatos (JSON, Parquet)
- [ ] Exportação em DOCX e PDF
- [ ] Análise temporal (comparação entre períodos)
- [ ] Mais tipos de visualizações
- [ ] Integração com outras LLMs
- [ ] Dashboard de métricas
- [ ] Sistema de templates personalizáveis

## 📄 Licença

MIT License - Sinta-se livre para usar e modificar

## 🙏 Agradecimentos

- Google AI pela API Gemini
- Hugging Face por hospedar a aplicação
- Comunidade Streamlit

---

**Desenvolvido com ❤️ para transformar a educação brasileira através de IA**

🤖 Powered by Google Gemini 2.5 Pro | 🎓 Foco em Educação
