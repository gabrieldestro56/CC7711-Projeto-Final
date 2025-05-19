from controller import Supervisor
import math
import random

# Insira aqui a quantidade de caixas que o robo terá de procurar
# O robo seguirá o mesmo padrão do exemplo "CAIXA01"
NUM_CAIXAS = 20 

# Configurações do Robo
MAX_VELOCIDADE = 6.28
TIME_STEP = 450
TOLERANCIA_DISTANCIA = 0.10
LIMITE_SENSOR = 150 # Melhor valor até o momento
MOVER = 1
EVASION_DURANTION = 5 

# ! FIM DAS CONFIGURAÇÕES ! #
# Armazena a última distância entre chamadas e contador de evasão
LastDist = float('inf')
EvasionCounter = 0

# sleep 
def sleep(supervisor, TIME_STEP, time_milisec=0):

    if time_milisec == 0:
        random_time = random.randint(1, 5)
        time_milisec = random_time * 100


    time_target = time_milisec / 1000.0
    init_time = supervisor.getTime()
    while supervisor.getTime() - init_time < time_target:
        supervisor.step(TIME_STEP)

# Função para gerar os objetivos das caixas
def GenerateCrateObjectives(posicoes_iniciais):
    objetivos = []
    for nome, (x, y) in posicoes_iniciais.items():
        objetivos.append((x, y))
    return objetivos

# Função para instanciar os sensores de proximidade
def InitializeSensors(supervisor):
    sensores = []
    for i in range(8):
        sensor = supervisor.getDevice(f"ps{i}")
        sensor.enable(TIME_STEP)
        sensores.append(sensor)
    return sensores

# Função auxiliar para calculo das distancias
def Distance2Points(x0, y0, xf, yf):
    return math.sqrt((xf - x0)**2 + (yf - y0)**2)

# Função para instanciar caixas e registrar posições iniciais
def GetCratesPosition(supervisor, num_caixas):
    caixas = []
    PosicoesIniciais = {}

    for i in range(num_caixas):
        nome_def = f"CAIXA{i+1:02d}"
        caixa = supervisor.getFromDef(nome_def)

        if caixa is None:
            print(f"Caixa {nome_def} não existe. Certifique-se de que a nomenclatura está de acordo \"CAIXA01\"")
            continue

        caixas.append(caixa)
        pos = caixa.getPosition()
        PosicoesIniciais[nome_def] = (pos[0], pos[1])

    return caixas, PosicoesIniciais

# ler sensores de proximidade
def ReadProximitySensors(sensores):
    leituras = []
    for sensor in sensores:
        valor = sensor.getValue()
        leituras.append(valor)
    return leituras

# Função para verificar se as caixas se moveram após tentativa de empurrão
def CheckCrateMoved(caixas, posicoes_iniciais, tolerancia=0.01):
    FinalPositions = {}

    for i, caixa in enumerate(caixas):
        nome = f"CAIXA{i+1:02d}"
        pos = caixa.getPosition()
        FinalPositions[nome] = (pos[0], pos[1])

    for nome in posicoes_iniciais:
        x0, y0 = posicoes_iniciais[nome]
        xf, yf = FinalPositions[nome]

        dist = Distance2Points(x0, y0, xf, yf)

        if dist < tolerancia:
            print(f"{nome} / PESADA / DISTANCIA: {dist:.4f}")
        else:
            print(f"{nome} / LEVE / DISTANCIA: {dist:.4f}")

# Função para controlar o movimento do robô
def ControlMovement(robo_node, caixa_node, sensores, mEsquerdo, mDireito, limite_sensor=135):
    # Posição e distância
    PosRobot = robo_node.getField("translation").getSFVec3f()
    PosBox = caixa_node.getPosition()
    xRobot, yRobot = PosRobot[0], PosRobot[1]
    xBox, yBox = PosBox[0], PosBox[1]
    dx = xBox - xRobot
    dy = yBox - yRobot
    Distance = math.sqrt(dx**2 + dy**2)

    # Ângulo desejado e atual
    TargetAngle = math.atan2(dy, dx)
    CurrentRotation = robo_node.getField("rotation").getSFRotation()
    CurrentAngle = CurrentRotation[3] * (1 if CurrentRotation[1] >= 0 else -1)

    # Aplicando correção
    CorrectionFactor = TargetAngle - CurrentAngle
    CorrectionFactor = (CorrectionFactor + math.pi) % (2 * math.pi) - math.pi

    # Leitura dos sensores
    Leituras = ReadProximitySensors(sensores)
    Front = Leituras[0] + Leituras[7]

    # Verificando direção do impacto
    Right = sum(Leituras[1:4])
    Left = sum(Leituras[4:7])

    isRight = Right > Left

    Progress = Distance < LastDist - 0.003
    LastDist = Distance

    # evasão de obstáculo
    if EvasionCounter > 0:
        EvasionCounter -= 1
        mEsquerdo.setVelocity(-1.5)
        mDireito.setVelocity(1.5)
        print("Executando evasão temporária...")
        return

    # Detectou obstáculo 
    if Front > limite_sensor:
        EvasionCounter = EVASION_DURANTION
        mEsquerdo.setVelocity((isRight and -1 or 1) * 1.5)
        mDireito.setVelocity((isRight and 1 or 1) * 1.5)
        return

    # Gira totalmente
    if abs(CorrectionFactor) > 2.5:
        rot = 2.5 if CorrectionFactor > 0 else -2.5
        mEsquerdo.setVelocity(-rot)
        mDireito.setVelocity(rot)
        print("Giro completo.")
        sleep(supervisor, TIME_STEP, 500)
        return

    # Corrige se mal orientado e parado
    ErrorTolerance = 2.0 if Distance > 0.4 else 2.5
    if abs(CorrectionFactor) > ErrorTolerance and not Progress:
        rot = 2.0 if CorrectionFactor > 0 else -2.0
        mEsquerdo.setVelocity(-rot)
        mDireito.setVelocity(rot)
        print("Corrigindo rotação sem progresso.")
        sleep(supervisor, TIME_STEP, 0)
        return

    # Alinhado ou progredindo: navegação proporcional adaptativa
    k = 0.6 * (1.0 + Distance)
    v_base = 5.0
    ajuste = max(min(k * CorrectionFactor, v_base), -v_base)

    if abs(CorrectionFactor) < 0.1:
        vel_e = min(v_base, MAX_VELOCIDADE)
        vel_d = min(v_base, MAX_VELOCIDADE)
    else:
        vel_e = max(min(v_base - ajuste, MAX_VELOCIDADE), -MAX_VELOCIDADE)
        vel_d = max(min(v_base + ajuste, MAX_VELOCIDADE), -MAX_VELOCIDADE)

    mEsquerdo.setVelocity(vel_e)
    mDireito.setVelocity(vel_d)

# Função para navegar até a caixa
def NavigateToCrate(caixa_node, robo_node, sensores, mEsquerdo, mDireito, tolerancia=0.10):
    pos_robo = robo_node.getField("translation").getSFVec3f()
    pos_caixa = caixa_node.getPosition()

    x_robo, y_robo = pos_robo[0], pos_robo[1]
    x_caixa, y_caixa = pos_caixa[0], pos_caixa[1]

    dx = x_caixa - x_robo
    dy = y_caixa - y_robo
    distancia = math.sqrt(dx**2 + dy**2)
    print(f"Distância até a caixa: {distancia:.2f}")

    if round(distancia, 2) <= tolerancia:
        mEsquerdo.setVelocity(0.0)
        mDireito.setVelocity(0.0)
        print("Robo parou.")
        return True  # Chegou ao destino

    ControlMovement(robo_node, caixa_node, sensores, mEsquerdo, mDireito, LIMITE_SENSOR)
    return False  # Ainda em movimento

# Função para empurrar a caixa
def PushCrateForDuration(supervisor, mEsquerdo, mDireito, TIME_STEP, duracao_segundos=2):
    print("Empurrando a caixa...")
    mEsquerdo.setVelocity(MAX_VELOCIDADE)
    mDireito.setVelocity(MAX_VELOCIDADE)

    steps_necessarios = int((1000 * duracao_segundos) / TIME_STEP)
    for _ in range(steps_necessarios):
        supervisor.step(TIME_STEP)

    mEsquerdo.setVelocity(0.0)
    mDireito.setVelocity(0.0)
    print("Caixa empurrada com sucesso.")

def ShowSensorValue(sensores):
    nomes = [f"ps{i}" for i in range(len(sensores))]
    valores = [f"{sensor.getValue():6.1f}" for sensor in sensores]

    print("\nLeitura dos sensores de proximidade:")
    for nome, valor in zip(nomes, valores):
        print(f"  {nome}: {valor}")


def FindNearestCrate(robo_node, caixas_restantes):
    pos_robo = robo_node.getField("translation").getSFVec3f()
    x_robo, y_robo = pos_robo[0], pos_robo[1]

    menor_dist = float('inf')
    caixa_mais_proxima = None
    indice = -1

    for i, caixa in enumerate(caixas_restantes):
        pos = caixa.getPosition()
        x_caixa, y_caixa = pos[0], pos[1]
        dist = math.sqrt((x_caixa - x_robo)**2 + (y_caixa - y_robo)**2)
        if dist < menor_dist:
            menor_dist = dist
            caixa_mais_proxima = caixa
            indice = i

    return indice, caixa_mais_proxima

def SpinLighestCrate(supervisor, robo_node, mEsquerdo, mDireito, caixas, posicoes_iniciais, TIME_STEP, tolerancia=0.01):

    # Verifica quais caixas se moveram (leves)
    caixas_leves = []
    for i, caixa in enumerate(caixas):
        nome = f"CAIXA{i+1:02d}"
        pos_final = caixa.getPosition()
        x0, y0 = posicoes_iniciais[nome]
        xf, yf = pos_final[0], pos_final[1]
        dist = Distance2Points(x0, y0, xf, yf)
        if dist > tolerancia:
            caixas_leves.append((i, caixa, dist))

    if not caixas_leves:
        print("Nenhuma caixa leve foi detectada.")
        return

    # Escolhe a mais leve
    caixas_leves.sort(key=lambda x: -x[2])
    indice_leve, caixa_leve, _ = caixas_leves[0]
    print(f"Voltando para a caixa leve: CAIXA{indice_leve+1:02d}")

    # Navega até ela
    while supervisor.step(TIME_STEP) != -1:
        pos_robo = robo_node.getField("translation").getSFVec3f()
        pos_caixa = caixa_leve.getPosition()
        dx = pos_caixa[0] - pos_robo[0]
        dy = pos_caixa[1] - pos_robo[1]
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia < 0.12:
            break

        angulo_desejado = math.atan2(dy, dx)
        rot_robo = robo_node.getField("rotation").getSFRotation()
        angulo_atual = rot_robo[3] * (1 if rot_robo[1] >= 0 else -1)
        erro = angulo_desejado - angulo_atual
        erro = (erro + math.pi) % (2 * math.pi) - math.pi
        ajuste = max(min(erro * 2.0, 6.28), -6.28)
        mEsquerdo.setVelocity(max(min(3.0 - ajuste, 6.28), -6.28))
        mDireito.setVelocity(max(min(3.0 + ajuste, 6.28), -6.28))

    # Para e gira em frente à caixa leve indefinidamente
    print("Robo alinhado à caixa leve. Iniciando giro no lugar.")
    while supervisor.step(TIME_STEP) != -1:
        mEsquerdo.setVelocity(-2.0)
        mDireito.setVelocity(2.0)

def LightCrateDetected(caixas, posicoes_iniciais, tolerancia=0.01):
    for i, caixa in enumerate(caixas):
        nome = f"CAIXA{i+1:02d}"
        pos_final = caixa.getPosition()
        x0, y0 = posicoes_iniciais[nome]
        xf, yf = pos_final[0], pos_final[1]
        dist = Distance2Points(x0, y0, xf, yf)
        if dist > tolerancia:
            return True  # há pelo menos uma caixa leve detectada
    return False

# Robo
supervisor = Supervisor()
mEsquerdo = supervisor.getDevice("left wheel motor")
mDireito = supervisor.getDevice("right wheel motor")
mEsquerdo.setPosition(float('inf'))
mDireito.setPosition(float('inf'))
Sensores = InitializeSensors(supervisor)

# Caixas
Caixas, PosicoesIniciais = GetCratesPosition(supervisor, NUM_CAIXAS)
objetivos_caixas = GenerateCrateObjectives(PosicoesIniciais)
robo_node = supervisor.getFromDef("ROBO")
CaixasRestantes = Caixas.copy()

while supervisor.step(TIME_STEP) != -1:

    # Não há mais caixas
    if not CaixasRestantes:
        print("Todas as caixas foram empurradas")
        CheckCrateMoved(Caixas, PosicoesIniciais)
        SpinLighestCrate(supervisor, robo_node, mEsquerdo, mDireito,Caixas, PosicoesIniciais, TIME_STEP)
        break
        
    # Encontra a caixa mais proxima
    LocalIndex, DestinationCrate = FindNearestCrate(robo_node, CaixasRestantes)

    # Navega até ela
    chegou = NavigateToCrate(DestinationCrate, robo_node, Sensores, mEsquerdo, mDireito)

    if not chegou:
        print("Robo ainda está em percurso...")
        continue

    # Aqui o robo chegou
    print(f"Robo chegou na CAIXA{LocalIndex+1:02d}")
    PushCrateForDuration(supervisor, mEsquerdo, mDireito, TIME_STEP, duracao_segundos=2)
    CaixasRestantes.pop(LocalIndex)

    if not LightCrateDetected(Caixas, PosicoesIniciais):
        continue

    # Aqui o robo encontrou a caixa leve
    print("Caixa leve encontrada, busca interrompida.")

    CheckCrateMoved(Caixas, PosicoesIniciais)
    SpinLighestCrate(supervisor, robo_node, mEsquerdo, mDireito, Caixas, PosicoesIniciais, TIME_STEP)

    break