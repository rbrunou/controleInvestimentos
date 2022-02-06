# pip list
# pip install openpyxl
# pip install dataframe_image
# pip install yfinance
# pip install seaborn
# pip install ipython
import yfinance as yf
import pandas as pd
import json
from datetime import date, datetime
import numpy as np
from datetime import timedelta
import seaborn as sns
from matplotlib import pyplot as plt
from IPython.display import clear_output

#Importa dados da planilha de planilha_investido e usa a data como index
planilha_investido = pd.read_excel('./Dados.xlsx', index_col = 0)
clear_output()

#Separo os dias que houveram 1 ou mais planilha_investido
dias_de_aporte = planilha_investido.index.unique()

#Gera um conjunto de datas do primeiro dia que foi feito investimento, até hoje
dti = pd.bdate_range(dias_de_aporte[0], date.today(), freq="D")

###################################################################################################
#Gerar um dataframe com todos os dias do primeiro aporte até hoje, e armazena no dia o 
#aporte total feito
investido = pd.DataFrame(index = dti)
investido['Investido'] = np.zeros(investido.shape[0])
for i in range(len(dias_de_aporte)):
    investido.loc[dias_de_aporte[i]]['Investido'] = round(planilha_investido.loc[planilha_investido.index == dias_de_aporte[i]]['Total Investido'].sum(),2)
###################################################################################################

###################################################################################################
#Verifica se houve investimento, se houver, soma com o anterior, senão repete o investido do dia anterior
for i in range(investido.shape[0]):
    if(investido.iloc[i][0] == 0):
        investido.iloc[i][0] = investido.iloc[i-1][0]
    else:
	    if(i!=0):
	        investido.iloc[i][0] = investido.iloc[i][0]+investido.iloc[i-1][0]
###################################################################################################

###################################################################################################
#Cria um dataframe com todos os dias desde o primeiro investimento
#Separa os ativos investidos pela coluna de tipos. Isso é necessário por conta da forma
#que é escrito o ticket no yahoo finance
#Todos os ativos são concatenados para a requisição no yahoo
cotacoes_importadas_yahoo = pd.DataFrame(index = dti)
ativos_para_baixar = ''
RVN = planilha_investido.loc[planilha_investido['Tipo'] == 'RV-N'].Ativo.unique()
for i in range(len(RVN)):
    ativos_para_baixar = ativos_para_baixar + RVN[i] + '.SA' + ','
    
RVI = planilha_investido.loc[planilha_investido['Tipo'] == 'RV-I'].Ativo.unique()
for i in range(len(RVI)):
    ativos_para_baixar = ativos_para_baixar + RVI[i] + ','
    
CRIPTO = planilha_investido.loc[planilha_investido['Tipo'] == 'CRIPTO'].Ativo.unique()
for i in range(len(CRIPTO)):
    ativos_para_baixar = ativos_para_baixar + CRIPTO[i] + '-USD' + ','
    
ativos_para_baixar = ativos_para_baixar + 'BRL=X,' + '^BVSP,' + '^GSPC'
###################################################################################################

###################################################################################################
#Baixando cotações do yahoo finance
print("Baixando Cotações")
cotacoes_importadas_yahoo = yf.download(ativos_para_baixar, start=dias_de_aporte[0])[['Adj Close']]
cotacoes_importadas_yahoo = cotacoes_importadas_yahoo.loc[:, 'Adj Close']
###################################################################################################

###################################################################################################
#Transferindo os dados importados para outro dataframe com identificações legíveis
#Para ativos cotados em dólar, faz-se uma multiplicação pela cotação do dólar
cotacoes_importadas = pd.DataFrame(index = dti)
for i in range(len(RVN)):
    cotacoes_importadas[RVN[i]] = cotacoes_importadas_yahoo.loc[:, RVN[i] + '.SA']

cotacoes_importadas['USDBRL'] = cotacoes_importadas_yahoo.loc[:, 'BRL=X'] 
    
for i in range(len(RVI)):
    cotacoes_importadas[RVI[i]] = cotacoes_importadas_yahoo.loc[:, RVI[i]] * cotacoes_importadas_yahoo.loc[:, 'BRL=X'] 
    
for i in range(len(CRIPTO)):
    cotacoes_importadas[CRIPTO[i]] = cotacoes_importadas_yahoo.loc[:, CRIPTO[i] + '-USD'] * cotacoes_importadas_yahoo.loc[:, 'BRL=X'] 

cotacoes_importadas['ACRIABRL'] = planilha_investido.loc[planilha_investido['Ativo'] == 'ACRIABRL']["Valor"]
###################################################################################################

###################################################################################################
#Inserindo colunas com dados de renda fixa
cotacoes_importadas['TESOUROIPCA'] = planilha_investido.loc[planilha_investido['Ativo'] == 'TESOUROIPCA']["Valor"]
cotacoes_importadas['TESOUROSELIC'] = planilha_investido.loc[planilha_investido['Ativo'] == 'TESOUROSELIC']["Valor"]

cotacoes_importadas['CDBIPCA'] = np.ones(len(cotacoes_importadas.index))
cotacoes_importadas['NUBANK'] = np.ones(len(cotacoes_importadas.index))
###################################################################################################

###################################################################################################
#Tratando os dados.
#Primeiro preenche os dados vazios com os valores anteriores
#Depois preenche os valores que persistirem vazios com 0
cotacoes_importadas.fillna(method='ffill', inplace=True)
cotacoes_importadas.fillna(0, inplace=True)
###################################################################################################

###################################################################################################
#Armazena o valor investido diariamente em colunas separadas no dataframe
investido_ativos = pd.DataFrame(index = dti)
aportado = planilha_investido.Ativo.unique()
for i in range(len(aportado)):
    investido_ativos[aportado[i]] = planilha_investido.loc[planilha_investido.Ativo == aportado[i]]["Total Investido"]

#Preenche os valores 'nan' do dataframe anteriormente criado para gerar um dataframe com valores
#acumulados de investimentos.
for j in range(investido_ativos.shape[1]):
    for i in range(investido_ativos.shape[0]):
        if(pd.isnull(investido_ativos.iat[i, j])):
            if(i==0):
                investido_ativos.iat[i, j]=0
            else:
                investido_ativos.iat[i, j] = investido_ativos.iat[i-1, j]
        else:
            if(i!=0):
                investido_ativos.iat[i, j] += investido_ativos.iat[i-1, j]
###################################################################################################

###################################################################################################
#Verifica quais ativos existem aporte, e posiciona o valor do aporte no dia e coluna do 
#dataframe quantidade_ativos
quantidade_ativos = pd.DataFrame(index = dti)
aportado = planilha_investido.Ativo.unique()
for i in range(len(aportado)):
    quantidade_ativos[aportado[i]] = planilha_investido.loc[planilha_investido.Ativo == aportado[i]]["Quantidade"]

#Se na data analisada houver Nan, ou seja, nada, o valor 0 será atribuído na primeira data, 
#senão a data atual receberá o valor da data anterior.
#Agora se na data atual houver um valor, o valor será somado com o valor da data anterior.
#Assim é possível gerar um acumulado de quantidade de ativos
for j in range(quantidade_ativos.shape[1]):
    for i in range(quantidade_ativos.shape[0]):
        if(pd.isnull(quantidade_ativos.iat[i, j])):
            if(i==0):
                quantidade_ativos.iat[i, j]=0
            else:
                quantidade_ativos.iat[i, j] = quantidade_ativos.iat[i-1, j]
        else:
            if(i!=0):
                quantidade_ativos.iat[i, j] += quantidade_ativos.iat[i-1, j]
###################################################################################################

###################################################################################################
#A carteira consolidada será o produto da cotação com a quantidade de ativos que foram comprados.
carteira_consolidada = pd.DataFrame(index = dti)
carteira_consolidada = quantidade_ativos * cotacoes_importadas
###################################################################################################

###################################################################################################
#Cria um dataframe separado para armazenar a compilação dos dados da carteira, como o total, o 
#valor investido e a progressão do lucro
compilacao = pd.DataFrame(index = dti)
compilacao['Total'] = round(carteira_consolidada.sum(axis=1),2)
compilacao['Investido'] = investido
compilacao['Lucro %'] = round(((compilacao['Total'] / compilacao['Investido'])-1)*100,2)
###################################################################################################

###################################################################################################
#Cria um dataframe com o nome indices, para comparar os índices:
#IBOV, SP500, IPCA, IGPM e CDI
#Primeiro apenas copia os dados do IBOV e do SP500 importados do yahoo 
indices = pd.DataFrame(index = dti)
indices['IBOV']   =     cotacoes_importadas_yahoo.loc[:, '^BVSP']
indices['SP500']   =    cotacoes_importadas_yahoo.loc[:, '^GSPC']
indices.fillna(method='ffill', inplace=True)

#Para importar indicadores do banco central, foi criada a função consulta_bc
# https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries
def consulta_bc(codigo_bcb):
  url = 'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json'.format(codigo_bcb)
  df = pd.read_json(url)
  df['data'] = pd.to_datetime(df['data'], dayfirst=True)
  df.set_index('data', inplace=True)
  return df

#Importa os indicadores do banco central
print("")
print("Importando dados Banco Central")
indices['IPCA'] = consulta_bc(433)
indices['IGPM'] = consulta_bc(189)
indices['CDI'] = consulta_bc(12)

#Substitui todos os dados NAN para 0
indices.fillna(0, inplace=True)
###################################################################################################

###################################################################################################
#Cria um dataframe com os índices importados, de tal forma que consigamos analisálos de forma
#acumulada desde o primeiro investimento feito.
indices_acumulados = pd.DataFrame(index = dti)

#Calcula a porcentagem acumulada do IBOV
#(indices[0]['IBOV']*indices[1]['IBOV']*indices[n]['IBOV']-1)
#pct_change -> retorna a diferença percentual entre o dado atual e o anterior
#cumprod -> realiza a multiplicação acumulada entre os dados da coluna especificada
indices_acumulados['IBOV'] = round(((1+(indices['IBOV'].pct_change())).cumprod()-1)*100,2)
indices_acumulados.iloc[0]=0

indices_acumulados['SP500'] = round(((1+(indices['SP500'].pct_change())).cumprod()-1)*100,2)
indices_acumulados.iloc[0]=0

#Nos indicadores abaixo, o retorno do banco central já é em porcentagem, enquanto o SP500 e o 
#IBOV é em pontos
indices_acumulados['IPCA'] = round(((1+(indices['IPCA']/100)).cumprod()-1)*100,2)
indices_acumulados.iloc[0]=0

indices_acumulados['IGPM'] = round(((1+(indices['IGPM']/100)).cumprod()-1)*100,2)
indices_acumulados.iloc[0]=0

indices_acumulados['CDI'] = round(((1+(indices['CDI']/100)).cumprod()-1)*100,2)
indices_acumulados.iloc[0]=0

#Apenas copia os dados do dataframe compilação
indices_acumulados['Carteira'] = compilacao['Lucro %']
###################################################################################################

###################################################################################################
#gera um dataframe com os valores dos índices hoje para comparação diária
indices_acumulados_hoje = pd.DataFrame(index = ['IBOV', 'SP500', 'IPCA', 'IGPM', 'CDI', 'Carteira'], columns =['Resultado %'])
indices_acumulados_hoje.loc['IBOV']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['IBOV']
indices_acumulados_hoje.loc['SP500']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['SP500']
indices_acumulados_hoje.loc['IPCA']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['IPCA']
indices_acumulados_hoje.loc['IGPM']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['IGPM']
indices_acumulados_hoje.loc['CDI']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['CDI']
indices_acumulados_hoje.loc['Carteira']['Resultado %'] = indices_acumulados.iloc[indices_acumulados.shape[0]-1]['Carteira']

indices_acumulados_hoje.sort_values(by='Resultado %', axis=0, ascending=True, inplace=True)
###################################################################################################

###################################################################################################
#Cria uma lista com os ativos investidos com(distribuicao_ativos) e sem(distribuicao_investido) 
#lucro até a data de hoje
distribuicao_ativos = carteira_consolidada.iloc[carteira_consolidada.shape[0]-1]
distribuicao_investido = investido_ativos.iloc[investido_ativos.shape[0]-1]
distribuicao_qt_ativos = quantidade_ativos.iloc[quantidade_ativos.shape[0]-1]

#Cria duas listas vazias para armazenar os rótulos e os valores dos ativos
#positivos contidos na carteira para geração de gráfico pizza
distribuicao_ativos_positivos_rotulos = []
distribuicao_ativos_positivos_valores = []
distribuicao_investido_positivos_rotulos = []
distribuicao_investido_positivos_valores = []

#Armazena apenas valores maiores que zero nos rótulos e valores para ativos com lucro
for i in range(len(distribuicao_ativos.values)):
    if distribuicao_ativos[i] > 0:
        distribuicao_ativos_positivos_rotulos.append(distribuicao_ativos.index[i])
        distribuicao_ativos_positivos_valores.append(distribuicao_ativos[i])

#Armazena apenas valores maiores que zero nos rótulos e valores para ativos sem lucro
for i in range(len(distribuicao_investido.values)):
    if ((distribuicao_investido[i] * distribuicao_qt_ativos[i]) > 0) and (distribuicao_investido[i] > 0):
        distribuicao_investido_positivos_rotulos.append(distribuicao_investido.index[i])
        distribuicao_investido_positivos_valores.append(distribuicao_investido[i])
###################################################################################################

###################################################################################################
#Gera o resultado compilado de valor total investido, o patrimônio total e a porcentagem de ganho
hoje = datetime.today().strftime('%Y-%m-%d')
ontem = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
ganho_hoje = compilacao.loc[hoje]['Total'] - compilacao.loc[ontem]['Total']
p_ganho_hoje = ((compilacao.loc[hoje]['Total'] / compilacao.loc[ontem]['Total'])-1)*100

compilado = pd.DataFrame(index = ['Resultados'], columns =['Investido', 'Patrimônio', 'Ganho'])
compilado.loc['Resultados']['Investido'] = 'R$' + str(round(compilacao.loc[hoje]['Investido'],2))
compilado.loc['Resultados']["Patrimônio"] = 'R$' + str(round(compilacao.loc[hoje]['Total'],2))
compilado.loc['Resultados']['Ganho'] = str(round(compilacao.loc[hoje]['Lucro %'],2)) + '%'
###################################################################################################

###################################################################################################
#Gera resultado compilado de valor ganho/perdido hoje e porcentagem do resultado.
compilado2 = pd.DataFrame(index = ['Resultados'], columns =['Hoje', '%'])
compilado2.loc['Resultados']["Hoje"] = 'R$' + str(round(ganho_hoje,2))
compilado2.loc['Resultados']["%"] = str(round(p_ganho_hoje,2)) + '%'
###################################################################################################

###################################################################################################
#Cria um dataframe com a soma da quantidade total em posse de cada ativo, valor total investido, 
#valor total dos investimentos hoje com a valorização/desvalorização e a porcentagem de ganho
#para cada ativo
resultado_geral = pd.DataFrame(planilha_investido.groupby(['Ativo']).Quantidade.sum())
resultado_geral['Investido'] = planilha_investido.groupby(['Ativo'])['Total Investido'].sum()

#Cria uma coluna com valores zerados
resultado_geral['Hoje'] = np.zeros(resultado_geral.shape[0])
resultado_geral['%'] = np.zeros(resultado_geral.shape[0])

#Calcula os valores da carteira hoje em reais e a % ganha em cada ativo
for i in range(resultado_geral.shape[0]):
    #armazena na coluna Hoje, a multiplicação da quantidade de ativos pela cotação no dia atual
    #resultado_geral.columns.get_loc('Hoje') -> retorna o índice da coluna Hoje para executar
    #a operação dentro do for
    resultado_geral.iat[i, resultado_geral.columns.get_loc('Hoje')] = round(resultado_geral.iat[i, resultado_geral.columns.get_loc('Quantidade')] * cotacoes_importadas.loc[hoje][resultado_geral.index[i]],2)
    #realiza um filtro para que se o valor investido ou o valor do capital hoje for menor que 0,
    #armazena 0 na coluna %
    if ((resultado_geral.iat[i, resultado_geral.columns.get_loc('Investido')] <= 0) or (resultado_geral.iat[i, resultado_geral.columns.get_loc('Hoje')] <= 0)):
        resultado_geral.iat[i, resultado_geral.columns.get_loc('%')] = 0
    #senão, armazena na coluna %, a relação porcentual entre o valor de hoje, com o valor investido
    else:
        resultado_geral.iat[i, resultado_geral.columns.get_loc('%')] = round(((resultado_geral.iat[i, resultado_geral.columns.get_loc('Hoje')] / resultado_geral.iat[i, resultado_geral.columns.get_loc('Investido')])-1)*100,2)                                 

#reliza uma organização crescente das linha com referência da coluna %
resultado_geral.sort_values(by='%', axis=0, ascending=False, inplace=True)

#armazena na coluna diferença o valor ganho em R$ do valor investido em relação a hoje
resultado_geral['Diferença'] = round(resultado_geral['Hoje'] - resultado_geral['Investido'],2)
###################################################################################################

###################################################################################################
#Gera uma tabela formatada para exportar como imagem
#realiza um filtro no resultado_geral para mostrar apenas onde o investimento que existe hoje seja 
#maior que 0, da coluna investido em diante
filtrado_resultado_geral = resultado_geral.loc[resultado_geral['Hoje']>0, 'Investido':]
#reorganiza as colunas do dataframe
filtrado_resultado_geral = filtrado_resultado_geral.reindex(columns=['Investido', 'Hoje', 'Diferença', '%'])

#soma todos os valores da coluna Investido
investido_total = filtrado_resultado_geral.Investido.sum(axis=0)
#soma todos os valores da coluna Hoje
investido_com_rendimentos = filtrado_resultado_geral.Hoje.sum(axis=0)
#cria um dataframe com os resultados da soma dos valores investido, com o valor do patrimônio Hoje
#a diferença total e a % de relação para uma linha com nome Total
total = pd.DataFrame({'Investido':[investido_total], 
                      'Hoje':[investido_com_rendimentos],
                      'Diferença':[investido_com_rendimentos - investido_total], 
                      '%':[(investido_com_rendimentos/investido_total-1)*100]},
                      index=['Total'])
#insere o dataframe total na última linha do dataframe filtrado resultado geral
filtrado_resultado_geral = filtrado_resultado_geral.append(total)
#gera uma função para preencher célular com cores de acordo com seus valores
def color_pos_neg_value(value):
    if value < 0:
        color = 'red'
    elif value > 0:
        color = 'green'
    else:
        color = 'nan'
    return 'background: %s' % color

#Gera um dataframe estilizado com cores, além de gerar uma imagem.
styled_resultado_geral = filtrado_resultado_geral.style.format(
                          {'Investido': "R$""{:.2f}",
                          'Hoje': "R$""{:.2f}",
                          '%': "{:.2f}""%",
                          'Diferença': "R$""{:.2f}",
                          }).applymap(color_pos_neg_value, subset=['%'])
###################################################################################################

###################################################################################################
#gera um dataframe com todos os meses desde o começo dos investimentos para compilar os dados mensais
mti = pd.bdate_range(dias_de_aporte[0], date.today(), freq="m")
mti = mti.strftime('%Y-%m-%d').tolist()
mti.append(date.today().strftime('%Y-%m-%d'))

carteira_consolidada_mes = pd.DataFrame(index = mti)

#pega o valor da carteira no fim de cada mês(mti[i]) e armazena em uma lista
consolidado_mes = []
for i in range(len(carteira_consolidada_mes)):
    if i == 0:
        consolidado_mes.append(compilacao.loc[compilacao.index == mti[i]].Total[0])
    else:
        consolidado_mes.append(compilacao.loc[compilacao.index == mti[i]].Total[0] - compilacao.loc[compilacao.index == mti[i-1]].Total[0])

#copia os dados da lista para o dataframe
carteira_consolidada_mes['Total'] = consolidado_mes
#gera mais uma coluna com os valores acumulados da carteira
carteira_consolidada_mes['Total_acc'] = carteira_consolidada_mes['Total'].cumsum()
###################################################################################################

###################################################################################################
#gera um dataframe com todos os anos desde o começo dos investimentos para compilar os dados anuais
ati = pd.bdate_range(dias_de_aporte[0], date.today(), freq="y")
ati = ati.strftime('%Y-%m-%d').tolist()
ati.append(date.today().strftime('%Y-%m-%d'))

carteira_consolidada_ano = pd.DataFrame(index = ati)

#pega o valor da carteira no fim de cada ano(ati[i]) e armazena em uma lista
consolidado_ano = []
for i in range(len(carteira_consolidada_ano)):
    if i == 0:
        consolidado_ano.append(compilacao.loc[compilacao.index == ati[i]].Total[0])
    else:
        consolidado_ano.append(compilacao.loc[compilacao.index == ati[i]].Total[0] - compilacao.loc[compilacao.index == ati[i-1]].Total[0])

#copia os dados da lista para o dataframe
carteira_consolidada_ano['Total'] = consolidado_ano
#gera mais uma coluna com os valores acumulados da carteira
carteira_consolidada_ano['Total_acc'] = carteira_consolidada_ano['Total'].cumsum()
###################################################################################################

###################################################################################################
print("")
print(compilado2)
print("")

print("")
print(filtrado_resultado_geral)
print("")

print("")
print(carteira_consolidada_mes)
print("")

print("")
print(carteira_consolidada_ano)
print("")
###################################################################################################

###################################################################################################
sns.set_style('darkgrid')
degrees = 90  # Adjust according to one's preferences/needs

area1 = plt.figure()

a1 = area1.add_subplot(2,2,1)
a1.set_title('Evolução Patrimonial Diária', loc='left', fontsize=18)
a1.set_ylabel('Retorno (R$)', fontsize=14)
plt.xticks([])
sns.lineplot(data=compilacao.loc[:, :'Investido'], palette='deep')

a2 = area1.add_subplot(2,2,2)
sns.set_palette("husl", 15)
sns.set_style('darkgrid')
a2.set_title('Acumulado Anual', loc='left', fontsize=18)
a2.tick_params(labelsize=13)
sns.barplot(x=carteira_consolidada_ano.index, y='Total_acc', data=carteira_consolidada_ano, palette='deep')
a2.set_ylabel('Total (R$)', fontsize=13)
for p in a2.patches:
    a2.text(p.get_x() + p.get_width()/2., p.get_height(), '%d' % int(p.get_height()), 
            fontsize=12, color='black', ha='center', va='bottom')
plt.xticks([])
plt.yticks([])

a3 = area1.add_subplot(2,2,3)
sns.set_palette("husl", 15)
sns.set_style('darkgrid')
a3.set_title('Comparação Geral Índices', loc='left', fontsize=18)
a3.set_xlabel('Período', fontsize=14)
plt.yticks([])
a3.set_ylabel('Total (%)', fontsize=14)
a3.tick_params(labelsize=13)
sns.barplot(x=indices_acumulados_hoje.index, y=indices_acumulados_hoje['Resultado %'], data=indices_acumulados_hoje, palette='deep')
for p in a3.patches:
    a3.text(p.get_x() + p.get_width()/2., p.get_height(), '%d' % int(p.get_height()), 
            fontsize=12, color='black', ha='center', va='bottom')

a4 = area1.add_subplot(2,2,4)
sns.set_palette("husl", 15)
sns.set_style('darkgrid')
a4.set_title('Acumulado Mensal', loc='left', fontsize=18)
a4.set_xlabel('Período', fontsize=14)
plt.yticks([])
a4.tick_params(labelsize=9)
plt.xticks(rotation=degrees)
sns.barplot(x=carteira_consolidada_mes.index, y='Total_acc', data=carteira_consolidada_mes, palette='YlOrRd')
a4.set_ylabel('Total (R$)', fontsize=13)
for p in a4.patches:
    a4.text(p.get_x() + p.get_width()/2., p.get_height(), '%d' % int(p.get_height()), 
            fontsize=9, color='black', ha='center', va='bottom',rotation=degrees)

plt.show()
print("")
print("Análise Finalizada")
print("")