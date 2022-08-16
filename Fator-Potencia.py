import PySimpleGUI as sg #criar front-end
import math as mt #cálculos matemáticos
import matplotlib.pyplot as plt #criar gráficos
import numpy as np #matrizes
import pulp as pp #cálculos de otimização 

class Fator:
  #Entrada de Dados Pativa,Preativa e fator de potência desejado 0.95 ou 0.92
  def __init__(self,Tensao,Pativa,Preativa,fatorfinal):
  
    #Transforma a Pativa, Preativa e fator de potência final desejado em tipo Float
    self.Tensao=float(Tensao)
    self.Pativa=float(Pativa)
    self.Preativa=float(Preativa)
    self.fatorfinal=float(fatorfinal)
      
    #Cálculo da Potência Aparente atual
    self.Paparente=mt.sqrt((self.Pativa**2)+(self.Preativa**2))
      
    #Cálculo do Fator de Potência atual
    self.fatoratual=(self.Pativa)/(self.Paparente)



    #Cálculo da quantidade de Potência reativa que deve adicionar ao sistema para corrigir o fator para 0.95
    if self.fatorfinal==0.92:
      self.Paparentefinal=self.Pativa/0.92
      self.Preativafinal=mt.sqrt((self.Paparentefinal**2)-(self.Pativa**2))
      self.Pbanco=self.Preativa-self.Preativafinal

    #Cálculo da quantidade de Potência reativa que deve adicionar ao sistema para corrigir o fator para 0.95
    else:
      self.Paparentefinal=self.Pativa/0.95
      self.Preativafinal=mt.sqrt((self.Paparentefinal**2)-(self.Pativa**2))
      self.Pbanco=self.Preativa-self.Preativafinal

    #Dados da tabela de capacitores de baixa tensão EasyCAN - 60Hz
    #[Qn(KVar),In(A),Capacitância(uF),Custo(R$)]
    self.Banco_220=np.array([[2.5,8.5,50.1,210.55],[5.5,17,100,300.19],[6.3,19.5,116,369.18],[11,34.1,200,481.40]])
    self.Banco_380=np.array([[1.1,1.7,6.6,59.51],[2.7,4.3,16.6,119.69],[3.2,5.2,19.9,136.66],[5.4,8.7,33.1,212.05],[8.1,13,49.7,298.01],[11.5,18,68.5,300.30],[13.5,21.7,82.9,414.38],[16.2,26,99.4,451.93],[21.7,34.6,133,573.09],[27.1,43.3,166,630.40]])
    self.Banco_440=np.array([[1.1,1.6,5.5,60.62],[2.2,3.1,11,110.21],[3.6,4.7,16.4,143.27],[6,7.8,27.4,212.61],[9,11.8,41.1,310.04],[12,15.7,54.8,389.6],[15,19.7,68.5,444.72],[20.3,26.6,92.6,564.49],[24,31.5,110,607.47],[30,39.4,137,727.83]])
    self.Banco_480=np.array([[5,6.1,19.3,208.95],[10.6,12.7,40.5,412.05],[12.5,15,47.9,458.47],[15,18,57.5,521.51],[20.4,24.5,78.3,647.59],[25,30,95.7,727.49],[31,37.2,119,833.81]])


    #Decisão sobre qual tensão aplicada e quais as quantidades de capacitores para o banco e seu valor
    if self.Tensao==220:
      (self.Capacitores,self.Qtde_Capacitores,self.custo_minimo)=self.Otimizacao_Banco(self.Pbanco,self.Banco_220)
    elif self.Tensao==380:
      (self.Capacitores,self.Qtde_Capacitores,self.custo_minimo)=self.Otimizacao_Banco(self.Pbanco,self.Banco_380)
    elif self.Tensao==440:
      (self.Capacitores,self.Qtde_Capacitores,self.custo_minimo)=self.Otimizacao_Banco(self.Pbanco,self.Banco_440)
    elif self.Tensao==480:
      (self.Capacitores,self.Qtde_Capacitores,self.custo_minimo)=self.Otimizacao_Banco(self.Pbanco,self.Banco_480)


    #Controladores
    self.Controladores=np.array([['Varlogic NR6',2923.42],['Varlogic NR12',3353.77]])
    self.Qtde_Capacitores_Total=0
    for i in self.Qtde_Capacitores:
      self.Qtde_Capacitores_Total+=i
    
    if self.Qtde_Capacitores_Total<=6:
      self.Controlador=self.Controladores[0]
    elif self.Qtde_Capacitores_Total>6 and self.Qtde_Capacitores_Total<12:
      self.Controlador=self.Controladores[1]
    elif self.Qtde_Capacitores_Total>12:
      self.Controlador='Número de estágios grande demais para controladores Varlogic.'
  
    self.comutador=149.37*self.Qtde_Capacitores_Total
    self.sinalizador=90.56*self.Qtde_Capacitores_Total
    self.armario=4086.05
    self.ventilacao=189.82*2
    self.contatora=496.89*self.Qtde_Capacitores_Total
    self.disjuntor=271.29*self.Qtde_Capacitores_Total
    self.disjuntor_geral=921.46
    

  #Mostra se com o Fator de Potência atual o cliente está pagando multa
  def Multa(self):
    if self.fatoratual<0.92:
      return ("PAGANDO MULTA")
    else:
      return ("SEM MULTA")


  #Monta o Triangulo de Potências
  def Grafico(self,ativa,reativa,reativabanco):
   
    #Triângulo com as potências iniciais
    plt.plot(np.arange(0,ativa+1,1), np.zeros(len(np.arange(0,ativa+1,1))), label="Potência Ativa",linewidth=3.0,color="b")
    plt.plot(np.ones(len(np.arange(0,reativa+1,1)))*ativa, np.arange(0,reativa+1,1), label="Potência Reativa",linewidth=3.0,color="g")
    plt.plot(np.linspace(0,ativa,len(np.arange(0,reativa,1))), np.linspace(0,reativa,len(np.arange(0,reativa,1))), label="Potência Aparente",linewidth=3.0,color="r")
    
    #Triângulo com as potências após o banco
    plt.plot(np.arange(0,ativa+0.01,0.01), np.zeros(len(np.arange(0,ativa+0.01,0.01))), label="Potência Ativa com Banco",linestyle="-",linewidth=5.0,color="b")
    plt.plot(np.ones(len(np.arange(0,reativabanco+0.01,0.01)))*ativa, np.arange(0,reativabanco+0.01,0.01), label="Potência Reativa com Banco",linestyle="-",linewidth=5.0,color="purple")
    plt.plot(np.linspace(0,ativa,len(np.arange(0,reativabanco,0.01))), np.linspace(0,reativabanco,len(np.arange(0,reativabanco,0.01))), label="Potência Aparente com Banco",linestyle="-",linewidth=5.0,color="gray")

    #Plotando
    plt.plot()

    plt.xlabel("Potência Ativa")
    plt.ylabel("Potência Reativa")
    plt.title("Triângulo de Potência")
    plt.legend()
    plt.grid()
    plt.show()


  def Otimizacao_Banco(self,Preativa,Banco):
    Preativa=float(Preativa)/1000
    i=0
    X=[]
    for i in range(len(Banco)):
      X.append(pp.LpVariable('Q'+str(Banco[i][0])+'KVar',cat="Integer",lowBound=0))
    EqPrincipal=0
    Restricao1=0
    Restricao2=0
    
    custo=pp.LpProblem('Minimo custo',pp.LpMinimize)

    i=0
    for i in range(len(Banco)):
      EqPrincipal+=Banco[i][3]*X[i]
    
    i=0
    for i in range(len(Banco)):
      Restricao1+=((Banco[i][0])*(X[i]))
    
    i=0
    for i in range(len(Banco)):
      Restricao2+=(X[i])
    
    custo+=EqPrincipal
    custo+=Restricao1>=Preativa
    custo+=Restricao2<=12
    
    custo.solve()
    
    custo_minimo=0
    Capacitores=[]
    Qtde_Capacitores=[]
    
    for l in range(len(custo.variables())):
      Capacitores.append(custo.variables()[l].name)
      Qtde_Capacitores.append(custo.variables()[l].varValue)
      custo_minimo+=custo.variables()[l].varValue*Banco[l][3]
    
    return (Capacitores,Qtde_Capacitores,round(custo_minimo,2))


  def retorna_Pativa(self):
    return round(self.Pativa,2)
  
  def retorna_Preativa(self):
    return round(self.Preativa,2)

  def retorna_Paparente(self):
    return round(self.Paparente,2)
  
  def retorna_fatoratual(self):
    return round(self.fatoratual,2)

  def retorna_Multa(self):
    return self.Multa()

  def retorna_Paparentefinal(self):
    return round(self.Paparentefinal,2)

  def retorna_Preativafinal(self):
    return round(self.Preativafinal,2)

  def retorna_Pbanco(self):
    return round(self.Pbanco,2)

  def retorna_Grafico(self):
    return self.Grafico(self.Pativa,self.Preativa,self.Preativafinal)

  def retorna_Capacitores(self):
    return self.Capacitores

  def retorna_Qtde_Capacitores(self):
    return self.Qtde_Capacitores
  
  def retorna_Custo_Minimo(self):
    return self.custo_minimo
    
  def retorna_Controlador(self):
    return self.Controlador[0]

  def retorna_Custo_Controlador(self):
    return self.Controlador[1]

  def retorna_componentes(self):
    return (self.comutador,self.sinalizador,self.armario,self.ventilacao,self.contatora,self.disjuntor,self.disjuntor_geral)

  def retorna_Custo_Total_Banco(self):
    return round(float(self.Controlador[1])+float(self.custo_minimo)+self.comutador+self.sinalizador+self.armario+self.ventilacao+self.contatora+self.disjuntor+self.disjuntor_geral,2)
    
def isnumber(value):
  try:
    float(value)
  except ValueError:
    return False
  return True

def janela_inicial():
  sg.theme('Reddit')
  layout = [[sg.Text('Bem- vindo(a) ao Fator de Potêcia Calculator!')],
            [sg.Text('Programa desenvolvido por aluno da UFRJ com o objetivo de dimensionar um banco de capacitores para corrigir o fator de potência da sua empresa.')],
            [sg.Button('Continuar',pad=(400,0))]
            ]
  return sg.Window('Bem-vindo(a)', layout=layout, finalize=True)

def janela_pot():
  sg.theme('Reddit')
  layout = [
            [sg.Text('Tensão (V)',size=(20,0)), sg.Input(key='tensao')],
            [sg.Text('Potência Ativa (W)',size=(20,0)), sg.Input(key='pativa')],
            [sg.Text('Potência Reativa (Var)',size=(20,0)), sg.Input(key='preativa')],
            [sg.Frame(layout=[[sg.Radio('0.92','Fator desejado',key='fator92'), sg.Radio('0.95','Fator desejado',key='fator95')]],title='Fator de Potência Final',pad=(208,0))],
            [sg.Button('Calcular Fator de Potência',pad=(200,0))]
  ]
  return sg.Window('Entrada de Dados', layout=layout, finalize=True)

def loading():
  # layout da janela
  sg.theme('Reddit')
  layout = [[sg.Text('Carregando')],
            [sg.ProgressBar(800, orientation='h', size=(20, 20), key='progressbar')],
            [sg.Cancel()]]

  # cria uma janela
  window = sg.Window('Carregando').Layout(layout)
  progress_bar = window.FindElement('progressbar')
  # loop para carregar
  for i in range(800):
      # checa pra ver se o butão de cancelar foi clicado e sai do loop
    event = window.Read(timeout=0)
    if event == 'Cancel'  or event is None:
      break
    # atializa a barra com valor do loop+1
    progress_bar.UpdateBar(i + 1)
  # Fecha a janela
  window.Close()


def janela_saidas():
  componentes=Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_componentes()
  col=[]
  capacitores=Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Capacitores()
  qtde_capacitores=Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Qtde_Capacitores()
  for i in range(len(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Capacitores())):
    if qtde_capacitores[i]!=0 and qtde_capacitores[i]>1:
      col.append([sg.Text(capacitores[i]),sg.Text(qtde_capacitores[i]),sg.Text('unidades')])
    elif qtde_capacitores[i]==1:
      col.append([sg.Text(capacitores[i]),sg.Text(qtde_capacitores[i]),sg.Text('unidade')])
  #grafico=Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Grafico()
  
  sg.theme('Reddit')
  layout = [
            [sg.Frame(layout=[
           [sg.Text('Potência Ativa:',size=(32,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Pativa()),sg.Text('W')],
            [sg.Text('Potência Reativa Inicial:',size=(32,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Preativa()),sg.Text('Var')],
            [sg.Text('Potência Aparente Inicial:',size=(32,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Paparente()),sg.Text('VA')],
            [sg.Text('Fator de Potência Inicial:',size=(32,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_fatoratual())],
            [sg.Text('Status da Multa:',size=(32,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Multa())]],title='Sem o Banco de Capacitores')],
            
            [sg.Frame(layout=[
            [sg.Text('Potência Ativa:',size=(36,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Pativa()),sg.Text('W')],
            [sg.Text('Potência Reativa com Banco:',size=(36,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Preativafinal()),sg.Text('Var')],
            [sg.Text('Potência Aparente com Banco:',size=(36,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Paparentefinal()),sg.Text('VA')],
            [sg.Text('Fator de Potência com Banco:',size=(36,0)), sg.Text(fatorfinal)],
            [sg.Text('Potência do Banco de Capacitores:',size=(36,0)), sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Pbanco()),sg.Text('Var')],
            [sg.Text("Status da Multa:",size=(36,0)),sg.Text("SEM MULTA")],
            #[sg.Image(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Grafico())],
            ],title='Com o Banco de Capacitores')],
            
            
            
            [sg.Frame(layout=[
            [sg.Text('Capacitores:',size=(35,0))],
            [sg.Column(col)],
            [sg.Text('Modelo do Controlador:',size=(35,0)),sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Controlador())],
            [sg.Text(' ')],
            [sg.Text('Custos:',size=(35,0))],
            [sg.Text('Capacitores:',size=(35,0)),sg.Text('R$'),sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Custo_Minimo())],
            [sg.Text('Controlador:',size=(35,0)),sg.Text('R$'),sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Custo_Controlador())],
            [sg.Text('Comutador:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[0])],
            [sg.Text('Sinalizador:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[1])],
            [sg.Text('Armário:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[2])],
            [sg.Text('Ventilação:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[3])],
            [sg.Text('Contatoras:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[4])],
            [sg.Text('Disjuntores:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[5])],
            [sg.Text('Disjuntor Geral:',size=(35,0)),sg.Text('R$'),sg.Text(componentes[6])],
            [sg.Text('-'*95)],
            [sg.Text('Custo Total:',size=(30,0),font=('bold')),sg.Text('R$',font=('bold')),sg.Text(Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Custo_Total_Banco(),font=('bold'))],
            ],title='Propriedades do Banco de Capacitores')],
            [sg.Button('Voltar',pad=(180,0))]
  ]
  return sg.Window('Relatório', layout=layout, finalize=True)

#Criar as janelas iniciais
janela1, janela2 ,janela3 = janela_inicial(), None, None


#Criar um loop de leitura de dados
while True:
  window, event, values = sg.read_all_windows()
  #Fechar as janelas
  if window == janela1 and event == sg.WIN_CLOSED:
    break
  if window == janela2 and event == sg.WIN_CLOSED:
    break
  if window == janela3 and event == sg.WIN_CLOSED:
    break

  
  #Quando queremos ir para a próxima janela
  if window == janela1 and event == "Continuar":
    janela2 = janela_pot()
    janela1.hide()
  
  if window == janela3 and event == "Voltar":
    janela3.hide()
    janela2.un_hide()



  if window == janela2 and event == "Calcular Fator de Potência" and isnumber(values['tensao'])==True and isnumber(values['pativa'])==True and isnumber(values['preativa'])==True and (values['fator92']==True or values['fator95']==True) and (values['tensao']=='220' or values['tensao']=='380' or values['tensao']=='440' or values['tensao']=='480'):
    Tensao=values['tensao']
    Pativa=values['pativa']
    Preativa=values['preativa']
    if values['fator92']==True:
      fatorfinal=0.92
    else:
      fatorfinal=0.95
    
    janela2.hide()
    loading()
    janela3=janela_saidas()
    grafico=Fator(Tensao,Pativa,Preativa,fatorfinal).retorna_Grafico()
    print(grafico)

  elif window == janela2 and event == "Calcular Fator de Potência" and values['fator92']==False and values['fator95']==False:
    sg.PopupOK('Marque o fator de potência desejado.')
  elif window == janela2 and event == "Calcular Fator de Potência" and (isnumber(values['tensao'])==False or isnumber(values['pativa'])==False or isnumber(values['preativa'])==False):
    sg.PopupOK('Digite um valor numérico.')
  elif window == janela2 and event == "Calcular Fator de Potência" and values['tensao']!=220 and values['tensao']!=380 and values['tensao']!=440 and values['tensao']!=480:
    sg.PopupOK('Somente valores de tensão padrão: 220V, 380V, 440V ou 480V.')
