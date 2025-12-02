from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np

app = Flask(__name__)
CORS(app)

def calcular_modalidade_otima(Df, Dp, Cp, Cf):
    """Calcula a modalidade ótima baseada nos históricos"""
    
    # Checando tamanho dos vetores
    amostra = len(Df)
    amostra2 = len(Dp)
    amostra3 = len(Cp)
    amostra4 = len(Cf)

    if not (amostra == amostra2 == amostra3 == amostra4):
        return {'error': 'As amostras de Demandas e Consumos devem ser do mesmo tamanho'}

    # Tarifas
    Tvcf = 0.34664
    Tvcp = 1.58306
    Tvd = 14.86

    Tacf = 0.34664
    Tacp = 0.49566
    Tadf = 14.86
    Tadp = 45.90

    # Encontrando valores mínimos e máximos
    Dminf = np.min(Df)
    Dminp = np.min(Dp)
    Dmin = np.minimum(Df, Dp)
    Dmint = np.min(Dmin)

    Dmaxf = np.max(Df)
    Dmaxp = np.max(Dp)
    D = np.maximum(Df, Dp)
    Dmaxt = int(np.max(D))

    # Modalidade Verde
    FatConV = 0
    Pcv = Cp * Tvcp + Cf * Tvcf
    for i in range(amostra):
        FatConV += Pcv[i]

    # Demanda Verde
    FatDemV = np.zeros(Dmaxt)
    Pvd = np.zeros(amostra)
    
    for j in range(Dmaxt):
        DcV = j + 1
        for i in range(amostra):
            if D[i] <= 1.05 * DcV:
                Pvd[i] = DcV * Tvd
            else:
                Pvd[i] = DcV * Tvd + 2 * (D[i] - DcV) * Tvd
            FatDemV[j] += Pvd[i]

    FatDemmintV = np.min(FatDemV)
    DcVotima = np.argmin(FatDemV) + 1
    PTV = FatConV + FatDemV[DcVotima - 1]

    # Modalidade Azul
    FatConA = 0
    Pca = Cp * Tacp + Cf * Tacf
    for i in range(amostra):
        FatConA += Pca[i]

    # Demanda Azul fora de ponta
    FatDemAf = np.zeros(int(Dmaxf - int(Dminf/1.1) + 1))
    Padf = np.zeros(amostra)
    
    for j in range(len(FatDemAf)):
        DcAf = j + int(Dminf/1.1)
        for i in range(amostra):
            if Df[i] <= 1.05 * DcAf:
                Padf[i] = DcAf * Tadf
            else:
                Padf[i] = DcAf * Tadf + 2 * (Df[i] - DcAf) * Tadf
            FatDemAf[j] += Padf[i]

    FatDemmintAf = np.min(FatDemAf)
    DcAfotima = np.argmin(FatDemAf)

    # Demanda Azul na ponta
    FatDemAp = np.zeros(int(Dmaxp - int(Dminp/1.1) + 1))
    Padp = np.zeros(amostra)
    
    for j in range(len(FatDemAp)):
        DcAp = j + int(Dminp/1.1)
        for i in range(amostra):
            if Dp[i] <= 1.05 * DcAp:
                Padp[i] = DcAp * Tadp
            else:
                Padp[i] = DcAp * Tadp + 2 * (Dp[i] - DcAp) * Tadp
            FatDemAp[j] += Padp[i]

    FatDemmintAp = np.min(FatDemAp)
    DcApotima = np.argmin(FatDemAp)

    PTA = FatConA + FatDemAf[DcAfotima] + FatDemAp[DcApotima]
    DcAfotima_final = DcAfotima + int(Dminf/1.1)
    DcApotima_final = DcApotima + int(Dminp/1.1)

    # Comparação das modalidades
    Menorcusto = min(PTV, PTA)
    modalidade = np.argmin([PTV, PTA]) + 1

    resultado = {
        'verde': {
            'custo_total': float(PTV),
            'demanda_contratada': int(DcVotima),
            'custo_consumo': float(FatConV),
            'custo_demanda': float(FatDemV[DcVotima - 1])
        },
        'azul': {
            'custo_total': float(PTA),
            'demanda_ponta': int(DcApotima_final),
            'demanda_fora_ponta': int(DcAfotima_final),
            'custo_consumo': float(FatConA),
            'custo_demanda_ponta': float(FatDemAp[DcApotima]),
            'custo_demanda_fora_ponta': float(FatDemAf[DcAfotima])
        },
        'modalidade_recomendada': 'verde' if modalidade == 1 else 'azul',
        'menor_custo': float(Menorcusto)
    }

    return resultado

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        data = request.get_json()
        
        # Converter os dados para arrays numpy
        Df = np.array([float(x) for x in data['demanda_hfp'].split()])
        Dp = np.array([float(x) for x in data['demanda_hp'].split()])
        Cp = np.array([float(x) for x in data['consumo_hp'].split()])
        Cf = np.array([float(x) for x in data['consumo_hfp'].split()])
        
        resultado = calcular_modalidade_otima(Df, Dp, Cp, Cf)
        
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True)