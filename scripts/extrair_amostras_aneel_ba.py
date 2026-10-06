import urllib3, requests, json, sys, pandas as pd
from pathlib import Path
from urllib3.util.ssl_ import create_urllib3_context

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
urllib3.disable_warnings()

ROOT = Path(__file__).resolve().parent.parent
AMOSTRAS = ROOT / "amostras"
AMOSTRAS.mkdir(exist_ok=True)

class NoSNIAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = 0
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

s = requests.Session()
s.mount('https://', NoSNIAdapter())

def ckan_get(action, params=None):
    url = f'https://200.198.220.169/api/3/action/{action}'
    r = s.get(url, params=params, headers={'Host': 'dadosabertos.aneel.gov.br'}, verify=False, timeout=90)
    return r.json().get('result', {})

print("1. Extraindo SIGA (BA)...")
res_siga = ckan_get('datastore_search', {
    'resource_id': '11ec447d-698d-4ab8-977f-b424d5deee6a',
    'filters': json.dumps({'SigUFPrincipal': 'BA'}),
    'limit': 2000
})
df_siga = pd.DataFrame(res_siga.get('records', []))
if '_id' in df_siga.columns: df_siga.drop(columns=['_id'], inplace=True)
siga_path = AMOSTRAS / "aneel_4.1_4.2_siga_geracao_BA.csv"
df_siga.to_csv(siga_path, index=False, encoding='utf-8-sig')
print(f"  Salvo: {siga_path.name} ({len(df_siga)} linhas)")

print("2. Extraindo P&D ANEEL (COELBA)...")
res_ped = ckan_get('datastore_search', {
    'resource_id': '3a7aee00-b6ee-4913-9670-f6b60f4a7bea',
    'limit': 5000
})
df_ped = pd.DataFrame(res_ped.get('records', []))
if not df_ped.empty and 'NomAgente' in df_ped.columns:
    df_ped = df_ped[df_ped['NomAgente'].str.contains('COELBA', case=False, na=False)].copy()
if '_id' in df_ped.columns: df_ped.drop(columns=['_id'], inplace=True)
ped_path = AMOSTRAS / "aneel_4.4_ped_projetos_COELBA.csv"
df_ped.to_csv(ped_path, index=False, encoding='utf-8-sig')
print(f"  Salvo: {ped_path.name} ({len(df_ped)} linhas)")

print("3. Extraindo INDQUAL Município (De/Para Conjunto -> Município BA)...")
res_indqual = ckan_get('datastore_search', {
    'resource_id': '3f841488-80a8-42f2-a6ca-e0c593b228de',
    'filters': json.dumps({'SigUF': 'BA'}),
    'limit': 3500
})
df_indqual = pd.DataFrame(res_indqual.get('records', []))
if '_id' in df_indqual.columns: df_indqual.drop(columns=['_id'], inplace=True)
indqual_path = AMOSTRAS / "aneel_4.5_indqual_conjunto_municipio_BA.csv"
df_indqual.to_csv(indqual_path, index=False, encoding='utf-8-sig')
print(f"  Salvo: {indqual_path.name} ({len(df_indqual)} linhas)")

print("4. Extraindo INDGER Comercial (UCs por Município BA - Amostra Recente)...")
res_indger = ckan_get('datastore_search', {
    'resource_id': 'fd10c9d4-cb76-4020-a322-e79afb13eaf7',
    'filters': json.dumps({'SigAgente': 'Neoenergia Coelba'}),
    'limit': 1500
})
df_indger = pd.DataFrame(res_indger.get('records', []))
if '_id' in df_indger.columns: df_indger.drop(columns=['_id'], inplace=True)
indger_path = AMOSTRAS / "aneel_4.3_indger_comercial_BA_amostra.csv"
df_indger.to_csv(indger_path, index=False, encoding='utf-8-sig')
print(f"  Salvo: {indger_path.name} ({len(df_indger)} linhas)")

print("5. Extraindo SAMP (Consumo / Classes COELBA - Amostra 2024)...")
res_samp = ckan_get('datastore_search', {
    'resource_id': 'ff80dd21-eade-4eb5-9ca8-d802c883940e',
    'filters': json.dumps({'SigAgenteDistribuidora': 'COELBA'}),
    'limit': 1000
})
df_samp = pd.DataFrame(res_samp.get('records', []))
if '_id' in df_samp.columns: df_samp.drop(columns=['_id'], inplace=True)
samp_path = AMOSTRAS / "aneel_4.3_samp_mercado_COELBA_amostra.csv"
df_samp.to_csv(samp_path, index=False, encoding='utf-8-sig')
print(f"  Salvo: {samp_path.name} ({len(df_samp)} linhas)")

print("\nConcluído com sucesso!")
