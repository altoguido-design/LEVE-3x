import yfinance as yf
import datetime

# Configurazione AGGIORNATA e corretta dei codici (ticker) da monitorare
TICKERS = {
    'MSTR_AZIONE': 'MSTR',             # Azione MicroStrategy (NASDAQ)
    'MSTR_LONG': 'MST3.L',             # MicroStrategy 3x Long (Europa)
    'MSTR_SHORT': '3SMI.MI',           # MicroStrategy 3x Short (Borsa Italiana)
    'COIN_AZIONE': 'COIN',             # Azione Coinbase Global (NASDAQ)
    'COIN_LONG': '3CON.MI',            # CORRETTO: Coinbase 3x Long (Borsa Italiana)
    'COIN_SHORT': 'S3CO.MI'            # CORRETTO: Coinbase 3x Short (Borsa Italiana)
}

def ottieni_dati_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d")
        if len(hist) >= 2:
            prezzo_chiusura = hist['Close'].iloc[-1]
            prezzo_precedente = hist['Close'].iloc[-2]
            var = ((prezzo_chiusura - prezzo_precedente) / prezzo_precedente) * 100
            return prezzo_chiusura, var
        else:
            info = t.fast_info
            return info.get('last_price', 0), info.get('regular_market_change_percent', 0) * 100
    except:
        return 0, 0

def interpreta_settore(nome_azione, var_azione, var_long, var_short):
    print(f"\n🧠 ANALISI STRUMENTI SU: {nome_azione}")
    print(f"   • Azione Base: {var_azione:+.2f}%")
    print(f"   • Certificato 3x LONG: {var_long:+.2f}%")
    print(f"   • Certificato 3x SHORT: {var_short:+.2f}%")
    print(f"   ---")
    
    if var_azione > 4:
        print("   Stato: 🚨 FORTE EUFORIA (FOMO)")
        print(f"   Cosa succede: Il titolo vola. Il Long 3x amplifica i guadagni ({var_long:+.2f}%), lo Short crolla.")
        print("   ⚠️ Consiglio comportamentale: NON INSEGUIRE IL RIALZO. Entrare adesso sui prodotti a leva "
              "significa esporsi al massimo rischio di ritracciamento. Rimani spettatore.")
    elif var_azione < -4:
        print("   Stato: 📉 PANIC SELLING (PAURA)")
        print(f"   Cosa succede: Il titolo crolla. Il Long subisce perdite pesantissime ({var_long:+.2f}%), lo Short vola.")
        print("   ⚠️ Consiglio comportamentale: NON TOCCARE I PRODOTTI LONG. Comprare pensando che 'abbia toccato il fondo' "
              "è un errore comune. La leva 3x distrugge i piccoli capitali in pochi giorni se il crollo continua.")
    else:
        print("   Stato: ⚖️ MOVIMENTO LATERALE (CALMA)")
        print("   Cosa succede: Il mercato oscilla poco.")
        print("   ⚠️ Consiglio comportamentale: ATTENZIONE ALL'EROSIONE da volatilità. Se l'azione va su e giù senza una direzione, "
              "i prodotti a leva perdono comunque valore ogni giorno per i costi matematici di mantenimento.")

def analizza_mercato():
    print("=" * 70)
    print("📊 RILEVATORE AUTOMATICO E INTERPRETE FINANZIARIO")
    print(f"⏱️ Momento della rilevazione: {datetime.datetime.now().strftime('%d/%m/%Y alle ore %H:%M:%S')}")
    print("🌐 Fonte dei dati: Yahoo Finance API (Dati di mercato)")
    print("=" * 70)
    
    dati = {}
    for nome, ticker in TICKERS.items():
        _, var = ottieni_dati_ticker(ticker)
        dati[nome] = var

    interpreta_settore("MICROSTRATEGY (MSTR)", dati['MSTR_AZIONE'], dati['MSTR_LONG'], dati['MSTR_SHORT'])
    print("-" * 70)
    interpreta_settore("COINBASE (COIN)", dati['COIN_AZIONE'], dati['COIN_LONG'], dati['COIN_SHORT'])
    print("=" * 70)

if __name__ == "__main__":
    analizza_mercato()
