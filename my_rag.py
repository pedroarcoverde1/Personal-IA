# Importando as bibliotecas necessárias
import os

import google.generativeai as genai
from dotenv import load_dotenv
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

# --- ETAPA 1: CONSTRUÇÃO DO GRAFO DE CONHECIMENTO (KG) ---

def criar_kg_sda():
    """
    Cria e popula um Grafo de Conhecimento sobre o universo de O Senhor dos Anéis.
    """
    # Criando um grafo vazio
    g = Graph()

    # Definindo um "Namespace" para nosso universo. Facilita a criação de URIs.
    SDA = Namespace("http://exemplo.org/senhordosaneis/")

    # --- Definindo Entidades (Nós do Grafo) ---
    frodo = SDA.Frodo
    anel = SDA.UmAnel
    sauron = SDA.Sauron
    gandalf = SDA.Gandalf
    mordor = SDA.Mordor
    condado = SDA.Condado
    
    # --- Definindo Relações (Arestas do Grafo) ---
    temPortador = SDA.temPortador
    éDaEspecie = SDA.éDaEspecie
    foiForjadoEm = SDA.foiForjadoEm
    éInimigoDe = SDA.éInimigoDe
    viveEm = SDA.viveEm
    
    # --- Adicionando as Triplas (Sujeito-Predicado-Objeto) ao Grafo ---
    # Fatos sobre o "Um Anel"
    g.add((anel, RDF.type, SDA.ArtefatoMagico))
    g.add((anel, foiForjadoEm, mordor))
    g.add((anel, RDFS.comment, Literal("Um anel para a todos governar.")))

    # Fatos sobre o Frodo
    g.add((frodo, RDF.type, SDA.Personagem))
    g.add((frodo, éDaEspecie, Literal("Hobbit")))
    g.add((frodo, viveEm, condado))
    g.add((frodo, temPortador, anel)) # Relação entre duas entidades

    # Fatos sobre o Gandalf
    g.add((gandalf, RDF.type, SDA.Personagem))
    g.add((gandalf, éDaEspecie, Literal("Maia")))
    g.add((gandalf, éInimigoDe, sauron))

    print("--> Grafo de Conhecimento criado com sucesso!")
    # Opcional: imprimir o grafo no formato Turtle para visualização
    # print(g.serialize(format='turtle'))
    
    return g

# --- ETAPA 2: IMPLEMENTAÇÃO DO RECUPERADOR (RETRIEVER) COM SPARQL ---

def recuperar_fatos(grafo, nome_entidade):
    """
    Recupera todos os fatos diretos sobre uma entidade no grafo usando SPARQL.
    """
    print(f"\n--> Buscando fatos sobre '{nome_entidade}' no Grafo...")
    
    # A consulta SPARQL. 
    # "SELECT ?p ?o" significa: selecione todos os predicados (?p) e objetos (?o)
    # "WHERE { sda:entidade ?p ?o . }" significa: onde o sujeito é a nossa entidade.
    query = f"""
        PREFIX sda: <http://exemplo.org/senhordosaneis/>
        SELECT ?predicado ?objeto
        WHERE {{
            sda:{nome_entidade} ?predicado ?objeto .
        }}
    """
    
    results = grafo.query(query)
    
    if not results:
        return "Nenhum fato encontrado sobre essa entidade."

    # Formatando os resultados para serem lidos por um humano (e pelo LLM)
    fatos_formatados = f"Contexto sobre {nome_entidade}:\n"
    for row in results:
        # Extrai o nome local da URI para facilitar a leitura
        predicado = row.predicado.split('/')[-1]
        objeto = row.objeto.split('/')[-1] if isinstance(row.objeto, URIRef) else row.objeto
        fatos_formatados += f"- {predicado}: {objeto}\n"
        
    print("--> Fatos recuperados:")
    print(fatos_formatados)
    return fatos_formatados

# --- ETAPA 3: INTEGRAÇÃO COM O GERADOR (LLM - GOOGLE GEMINI) ---

def gerar_resposta(contexto, pergunta):
    """
    Usa o modelo Gemini para gerar uma resposta baseada no contexto e na pergunta.
    """
    print("\n--> Enviando pergunta e contexto para o LLM...")
    
    # Carregando a chave de API do arquivo .env
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Chave de API do Google não encontrada. Verifique seu arquivo .env")
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Engenharia de Prompt: A instrução que damos ao LLM.
    # É CRUCIAL instruir o modelo a usar APENAS o contexto fornecido.
    prompt = f"""
    Você é um assistente especialista no universo de O Senhor dos Anéis.
    Sua tarefa é responder à pergunta do usuário usando APENAS as informações 
    fornecidas no contexto abaixo. Não use seu conhecimento prévio.

    **Contexto:**
    {contexto}

    **Pergunta:**
    {pergunta}

    **Resposta:**
    """
    
    response = model.generate_content(prompt)
    
    print("--> Resposta gerada pelo LLM:")
    return response.text

# --- JUNTANDO TUDO ---

if __name__ == "__main__":
    # 1. Construir a base de conhecimento
    meu_kg = criar_kg_sda()
    
    # 2. Definir a entidade e a pergunta que queremos fazer
    entidade_alvo = "Frodo"
    pergunta_usuario = "Me fale sobre o Frodo. Ele é portador de algum artefato?"

    # 3. Recuperar os fatos relevantes do KG
    contexto_recuperado = recuperar_fatos(meu_kg, entidade_alvo)
    
    # 4. Gerar uma resposta em linguagem natural usando os fatos recuperados
    if "Nenhum fato encontrado" not in contexto_recuperado:
        resposta_final = gerar_resposta(contexto_recuperado, pergunta_usuario)
        print(resposta_final)
