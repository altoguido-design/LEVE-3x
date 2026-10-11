import datetime

import plotly.graph_objects as go
import pytz
import streamlit as st
import yfinance as yf


# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="Rilevatore Leve 3x",
    page_icon="📊",
    layout="wide",
)

TZ_IT = pytz.timezone("Europe/Rome")
TZ_USA = pytz.timezone("America/New_York")

LEVA = 3.0


# ============================================================
# TICKER
# ============================================================

TICKERS = {
    "MSTR": {
        "nome": "MicroStrategy (MSTR)",
        "azione": "MSTR",
        "long": "3MST.MI",
        "short": "3SMI.MI",
    },
    "COIN": {
        "nome": "Coinbase (COIN)",
        "azione": "COIN",
        "long": "3CON.MI",
        "short": "S3CO.MI",
    },
}


# ============================================================
# ORARI
# ============================================================

def ora_italiana():
    return datetime.datetime.now(TZ_IT)


def ora_new_york():
    return datetime.datetime.now(TZ_USA)


# ============================================================
# STATO DEI MERCATI
# ============================================================

def calcola_stato_borse():

    ora_it = ora_italiana()
    ora_usa = ora_new_york()

    if ora_it.weekday() >= 5:
        return {
            "milano_aperta": False,
            "usa_aperta": False,
            "fase_usa": "CLOSE",
            "stato_milano": "🔴 CHIUSA (Weekend)",
            "stato_usa": "🔴 CHIUSA (Weekend)",
        }

    minuti_it = ora_it.hour * 60 + ora_it.minute

    milano_aperta = (
        9 * 60 <= minuti_it < 17 * 60 + 30
    )

    stato_milano = (
        "🟢 APERTA"
        if milano_aperta
        else "🔴 CHIUSA"
    )

    minuti_usa = ora_usa.hour * 60 + ora_usa.minute

    if 4 * 60 <= minuti_usa < 9 * 60 + 30:

        fase_usa = "PRE"
        stato_usa = "🟡 PRE-MARKET (Esteso)"
        usa_aperta = False

    elif 9 * 60 + 30 <= minuti_usa < 16 * 60:

        fase_usa = "REGULAR"
        stato_usa = "🟢 APERTA (Sessione Ordinaria)"
        usa_aperta = True

    elif 16 * 60 <= minuti_usa < 20 * 60:

        fase_usa = "POST"
        stato_usa = "🔵 POST-MARKET (Esteso)"
        usa_aperta = False

    else:

        fase_usa = "CLOSE"
        stato_usa = "🔴 CHIUSA"
        usa_aperta = False

    return {
        "milano_aperta": milano_aperta,
        "usa_aperta": usa_aperta,
        "fase_usa": fase_usa,
        "stato_milano": stato_milano,
        "stato_usa": stato_usa,
    }


# ============================================================
# DOWNLOAD DATI INTRADAY
# ============================================================

@st.cache_data(ttl=30, show_spinner=False)
def scarica_intraday(
    ticker,
    periodo="1d",
    intervallo="1m",
    prepost=False,
):

    try:

        df = yf.Ticker(ticker).history(
            period=periodo,
            interval=intervallo,
            prepost=prepost,
            auto_adjust=False,
        )

        if df is None or df.empty:
            return None

        if "Close" not in df.columns:
            return None

        df = df.dropna(subset=["Close"])

        if df.empty:
            return None

        return df

    except Exception:
        return None


# ============================================================
# DOWNLOAD DATI GIORNALIERI
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def scarica_daily(ticker):

    try:

        df = yf.Ticker(ticker).history(
            period="10d",
            interval="1d",
            auto_adjust=False,
        )

        if df is None or df.empty:
            return None

        if "Close" not in df.columns:
            return None

        df = df.dropna(subset=["Close"])

        if df.empty:
            return None

        return df

    except Exception:
        return None


# ============================================================
# VARIAZIONE PERCENTUALE
# ============================================================

def calcola_variazione(
    prezzo_attuale,
    prezzo_precedente,
):

    if prezzo_attuale is None:
        return None

    if prezzo_precedente is None:
        return None

    if prezzo_precedente == 0:
        return None

    return (
        (prezzo_attuale - prezzo_precedente)
        / prezzo_precedente
    ) * 100


# ============================================================
# DATI AZIONE USA
# ============================================================

def ottieni_dati_azione(ticker):

    intraday = scarica_intraday(
        ticker,
        periodo="5d",
        intervallo="1m",
        prepost=True,
    )

    daily = scarica_daily(ticker)

    if intraday is None:
        return {
            "prezzo": None,
            "variazione": None,
            "storico": None,
        }

    try:

        prezzo_attuale = float(
            intraday["Close"].iloc[-1]
        )

    except (TypeError, ValueError, IndexError):

        return {
            "prezzo": None,
            "variazione": None,
            "storico": intraday,
        }

    if daily is None or len(daily) < 2:

        return {
            "prezzo": prezzo_attuale,
            "variazione": None,
            "storico": intraday,
        }

    try:

        prezzo_precedente = float(
            daily["Close"].iloc[-2]
        )

    except (TypeError, ValueError, IndexError):

        return {
            "prezzo": prezzo_attuale,
            "variazione": None,
            "storico": intraday,
        }

    variazione = calcola_variazione(
        prezzo_attuale,
        prezzo_precedente,
    )

    return {
        "prezzo": prezzo_attuale,
        "variazione": variazione,
        "storico": intraday,
    }


# ============================================================
# DATI ETP ITALIANI
# ============================================================

def ottieni_dati_certificato(ticker):

    try:

        daily = scarica_daily(ticker)

        storico = scarica_intraday(
            ticker,
            periodo="5d",
            intervallo="1h",
            prepost=False,
        )

        if daily is None or daily.empty:

            return {
                "prezzo": None,
                "variazione": None,
                "storico": storico,
            }

        daily = daily.dropna(
            subset=["Close"]
        )

        if daily.empty:

            return {
                "prezzo": None,
                "variazione": None,
                "storico": storico,
            }

        prezzo = float(
            daily["Close"].iloc[-1]
        )

        if len(daily) >= 2:

            precedente = float(
                daily["Close"].iloc[-2]
            )

            variazione = calcola_variazione(
                prezzo,
                precedente,
            )

        else:

            variazione = None

        return {
            "prezzo": prezzo,
            "variazione": variazione,
            "storico": storico,
        }

    except Exception:

        return {
            "prezzo": None,
            "variazione": None,
            "storico": None,
        }


# ============================================================
# PREZZO USA ALLE 17:30
# ============================================================

def trova_prezzo_alle_1730(storico):

    if storico is None or storico.empty:
        return None

    try:

        indice = storico.index

        target = ora_italiana().replace(
            hour=17,
            minute=30,
            second=0,
            microsecond=0,
        )

        if getattr(indice, "tz", None) is not None:
            target = target.astimezone(indice.tz)

        validi = indice[indice <= target]

        if len(validi) == 0:
            return None

        timestamp = validi[-1]

        valore = storico.loc[
            timestamp,
            "Close",
        ]

        return float(valore)

    except Exception:
        return None


# ============================================================
# MOVIMENTO USA DOPO MILANO
# ============================================================

def calcola_movimento_post_milano(dati_azione):

    if dati_azione is None:
        return None

    storico = dati_azione.get("storico")
    prezzo_attuale = dati_azione.get("prezzo")

    if storico is None or storico.empty:
        return None

    if prezzo_attuale is None:
        return None

    prezzo_1730 = trova_prezzo_alle_1730(
        storico
    )

    if prezzo_1730 is None:
        return None

    return calcola_variazione(
        prezzo_attuale,
        prezzo_1730,
    )


# ============================================================
# LEVA TEORICA
# ============================================================

def calcola_3x_teorico(
    variazione_sottostante,
    direzione,
):

    if variazione_sottostante is None:
        return None

    if direzione == "LONG":
        return variazione_sottostante * LEVA

    if direzione == "SHORT":
        return variazione_sottostante * -LEVA

    return None


# ============================================================
# PREZZO TEORICO
# ============================================================

def calcola_prezzo_teorico(
    prezzo,
    variazione,
):

    if prezzo is None or variazione is None:
        return None

    return prezzo * (
        1 + variazione / 100
    )


# ============================================================
# CAMBIO EUR/USD
# ============================================================

def ottieni_cambio_eur_usd():

    try:

        intraday = scarica_intraday(
            "EURUSD=X",
            periodo="5d",
            intervallo="1h",
            prepost=False,
        )

        daily = scarica_daily(
            "EURUSD=X"
        )

        if intraday is None or intraday.empty:

            return {
                "prezzo": None,
                "variazione": None,
            }

        prezzo = float(
            intraday["Close"].iloc[-1]
        )

        variazione = None

        if daily is not None and len(daily) >= 2:

            precedente = float(
                daily["Close"].iloc[-2]
            )

            variazione = calcola_variazione(
                prezzo,
                precedente,
            )

        return {
            "prezzo": prezzo,
            "variazione": variazione,
        }

    except Exception:

        return {
            "prezzo": None,
            "variazione": None,
        }


# ============================================================
# CORREZIONE EUR/USD
# ============================================================

def correggi_per_eur_usd(
    movimento_usa,
    variazione_eur_usd,
):

    if movimento_usa is None:
        return None

    if variazione_eur_usd is None:
        return movimento_usa

    return (
        (
            1 + movimento_usa / 100
        )
        /
        (
            1 + variazione_eur_usd / 100
        )
        - 1
    ) * 100


# ============================================================
# FORMATTAZIONE
# ============================================================

def formatta_prezzo(
    prezzo,
    valuta,
    decimali=2,
):

    if prezzo is None:
        return "N/D"

    return (
        f"{prezzo:.{decimali}f} "
        f"{valuta}"
    )


def formatta_variazione(variazione):

    if variazione is None:
        return "N/D"

    return f"{variazione:+.2f}%"


# ============================================================
# INTERPRETAZIONE
# ============================================================

def interpreta_mercato(variazione):

    if variazione is None:

        return (
            "⚪ DATI NON DISPONIBILI",
            "Dati insufficienti.",
        )

    if variazione >= 4:

        return (
            "🚨 FORTE RIALZO",
            "Movimento molto forte.",
        )

    if variazione >= 1:

        return (
            "🟢 RIALZO",
            "Il sottostante è in rialzo.",
        )

    if variazione <= -4:

        return (
            "🚨 FORTE RIBASSO",
            "Movimento molto forte.",
        )

    if variazione <= -1:

        return (
            "🔴 RIBASSO",
            "Il sottostante è in ribasso.",
        )

    return (
        "⚖️ MOVIMENTO CONTENUTO",
        "Movimento contenuto.",
    )


# ============================================================
# BLOCCO STRUMENTO
# ============================================================

def mostra_blocco(
    chiave,
    dati,
    stato_mercati,
    cambio_eur_usd,
    colore_grafico,
):

    configurazione = TICKERS[chiave]

    st.header(
        configurazione["nome"]
    )

    azione = dati["azione"]
    long = dati["long"]
    short = dati["short"]

    # ========================================================
    # MERCATO USA
    # ========================================================

    st.subheader("🇺🇸 Mercato USA")

    prezzo_azione = formatta_prezzo(
        azione["prezzo"],
        "$",
    )

    variazione_azione = formatta_variazione(
        azione["variazione"]
    )

    fase = stato_mercati["fase_usa"]

    if fase == "PRE":
        tag_fase = "🟡 Pre-Market"

    elif fase == "REGULAR":
        tag_fase = "🟢 Live"

    elif fase == "POST":
        tag_fase = "🔵 Post-Market"

    else:
        tag_fase = "🔴 Chiuso"

    st.write(
        f"**Azione Base ({configurazione['azione']}):** "
        f"{prezzo_azione} "
        f"({variazione_azione}) "
        f"{tag_fase}"
    )

    st.caption(
        "💡 Ultima quotazione disponibile · "
        "variazione vs precedente chiusura"
    )

    # ========================================================
    # RELAZIONE 3X
    # ========================================================

    st.subheader(
        "📐 Relazione teorica 3x giornaliera"
    )

    variazione_base = azione["variazione"]

    long_teorico = calcola_3x_teorico(
        variazione_base,
        "LONG",
    )

    short_teorico = calcola_3x_teorico(
        variazione_base,
        "SHORT",
    )

    if variazione_base is not None:

        st.write(
            f"📊 Sottostante: "
            f"**{variazione_base:+.2f}%**"
        )

        st.write(
            f"🚀 **LONG 3x:** "
            f"{long_teorico:+.2f}%"
        )

        st.write(
            f"📉 **SHORT -3x:** "
            f"{short_teorico:+.2f}%"
        )

        st.caption(
            "🧮 Teorico: sottostante × ±3 · "
            "non è la performance reale dell'ETP"
        )

    else:

        st.info(
            "Dati insufficienti."
        )

    # ========================================================
    # ETP ITALIA
    # ========================================================

    st.subheader(
        "🇮🇹 ETP Italia — Borsa di Milano"
    )

    prezzo_long = formatta_prezzo(
        long["prezzo"],
        "€",
        4,
    )

    prezzo_short = formatta_prezzo(
        short["prezzo"],
        "€",
        4,
    )

    variazione_long = formatta_variazione(
        long["variazione"]
    )

    variazione_short = formatta_variazione(
        short["variazione"]
    )

    stato_certificati = (
        ""
        if stato_mercati["milano_aperta"]
        else " 🧊"
    )

    st.write(
        f"🚀 **ETP 3x LONG ({configurazione['long']}):** "
        f"{prezzo_long} "
        f"({variazione_long})"
        f"{stato_certificati}"
    )

    st.write(
        f"📉 **ETP -3x SHORT ({configurazione['short']}):** "
        f"{prezzo_short} "
        f"({variazione_short})"
        f"{stato_certificati}"
    )

    if not stato_mercati["milano_aperta"]:

        st.caption(
            "💡 🧊 Ultima quotazione disponibile · "
            "non live con Milano chiusa"
        )

    # ========================================================
    # STIMA PROSSIMA APERTURA
    # ========================================================

    if not stato_mercati["milano_aperta"]:

        st.subheader(
            "🔮 Stima teorica prossima apertura"
        )

        st.caption(
            "💡 Effetto teorico del movimento USA sul prezzo ETP"
        )

        movimento_post_milano = (
            calcola_movimento_post_milano(
                azione
            )
        )

        if movimento_post_milano is not None:

            st.write(
                f"🇺🇸 **Movimento USA:** "
                f"{movimento_post_milano:+.2f}%"
            )

            cambio_attuale = cambio_eur_usd.get(
                "prezzo"
            )

            cambio_variazione = cambio_eur_usd.get(
                "variazione"
            )

            if cambio_attuale is not None:

                st.write(
                    f"💱 **EUR/USD:** "
                    f"{cambio_attuale:.5f} "
                    f"({formatta_variazione(cambio_variazione)})"
                )

            movimento_corretto = (
                correggi_per_eur_usd(
                    movimento_post_milano,
                    cambio_variazione,
                )
            )

            if movimento_corretto is not None:

                st.write(
                    f"📊 **Stima teorica corretta "
                    f"per EUR/USD:** "
                    f"{movimento_corretto:+.2f}%"
                )

            long_post = calcola_3x_teorico(
                movimento_corretto,
                "LONG",
            )

            short_post = calcola_3x_teorico(
                movimento_corretto,
                "SHORT",
            )

            # ------------------------------------------------
            # LONG
            # ------------------------------------------------

            if long_post is not None:

                st.write(
                    f"🚀 **LONG 3x teorico:** "
                    f"{long_post:+.2f}%"
                )

                if long["prezzo"] is not None:

                    prezzo_long_teorico = (
                        calcola_prezzo_teorico(
                            long["prezzo"],
                            long_post,
                        )
                    )

                    st.write(
                        f"🧮 **Prezzo teorico LONG:** "
                        f"€{prezzo_long_teorico:.4f}"
                    )

            # ------------------------------------------------
            # SHORT
            # ------------------------------------------------

            if short_post is not None:

                st.write(
                    f"📉 **SHORT -3x teorico:** "
                    f"{short_post:+.2f}%"
                )

                if short["prezzo"] is not None:

                    prezzo_short_teorico = (
                        calcola_prezzo_teorico(
                            short["prezzo"],
                            short_post,
                        )
                    )

                    st.write(
                        f"🧮 **Prezzo teorico SHORT:** "
                        f"€{prezzo_short_teorico:.4f}"
                    )

            st.caption(
                "🧮 Prezzi teorici matematici · "
                "non sono quotazioni o previsioni reali"
            )

            st.warning(
                "⚠️ Il prezzo reale può differire per "
                "spread, liquidità, NAV, tracking difference, "
                "costi, ribilanciamento, gap e altri fattori."
            )

        else:

            st.info(
                "Dati USA insufficienti per la stima."
            )

    # ========================================================
    # GRAFICO
    # ========================================================

    storico = azione["storico"]

    if storico is not None and not storico.empty:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=storico.index,
                y=storico["Close"],
                mode="lines",
                name=configurazione["azione"],
                line=dict(
                    color=colore_grafico,
                    width=2,
                ),
            )
        )

        fig.update_layout(
            title=(
                f"📈 Grafico intraday "
                f"{configurazione['azione']}"
            ),
            margin=dict(
                l=20,
                r=20,
                t=40,
                b=20,
            ),
            height=250,
            template="plotly_dark",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "staticPlot": True,
                "displayModeBar": False,
                "scrollZoom": False,
                "doubleClick": False,
                "responsive": True,
            },
        )

        st.caption(
            "📊 Quotazioni intraday USA disponibili · "
            "pre/post-market quando presenti"
        )

    # ========================================================
    # INTERPRETAZIONE
    # ========================================================

    titolo_stato, consiglio = interpreta_mercato(
        azione["variazione"]
    )

    st.subheader(
        "🧠 Stato del Mercato & Interpretazione"
    )

    if "FORTE" in titolo_stato:
        st.error(titolo_stato)

    elif "RIALZO" in titolo_stato:
        st.success(titolo_stato)

    elif "RIBASSO" in titolo_stato:
        st.warning(titolo_stato)

    else:
        st.info(titolo_stato)

    st.write(consiglio)

    st.caption(
        "💡 Indicazione automatica descrittiva · "
        "non è una raccomandazione"
    )


# ============================================================
# PROGRAMMA PRINCIPALE
# ============================================================

def main():

    st.title(
        "📊 Rilevatore e Interprete Finanziario Leve 3x"
    )

    stato_mercati = calcola_stato_borse()

    # ========================================================
    # STATO MERCATI
    # ========================================================

    st.subheader(
        "🏛️ Stato Attuale dei Mercati"
    )

    col_info1, col_info2, col_info3 = st.columns(3)

    with col_info1:

        st.markdown(
            "**🇮🇹 BORSA ITALIANA (Milano):**\n\n"
            f"{stato_mercati['stato_milano']}"
        )

        st.caption(
            "09:00–17:30 · festività non considerate"
        )

    with col_info2:

        st.markdown(
            "**🇺🇸 BORSA AMERICANA (NASDAQ):**\n\n"
            f"{stato_mercati['stato_usa']}"
        )

        st.caption(
            "Pre 04:00–09:30 · Regular 09:30–16:00 · "
            "Post 16:00–20:00 NY"
        )

    with col_info3:

        st.markdown(
            f"⏱️ **Rilevazione:** "
            f"{ora_italiana().strftime('%d/%m/%Y - %H:%M:%S')}"
        )

        if st.button(
            "🔄 Aggiorna Prezzi Ora"
        ):

            st.cache_data.clear()
            st.rerun()

    # ========================================================
    # AVVISI
    # ========================================================

    if (
        not stato_mercati["milano_aperta"]
        and stato_mercati["fase_usa"]
        in ["PRE", "REGULAR", "POST"]
    ):

        st.info(
            "ℹ️ Milano è chiusa mentre gli USA sono attivi. "
            "Gli ETP mostrano l'ultima quotazione disponibile; "
            "l'azione USA continua a muoversi."
        )

    elif not stato_mercati["milano_aperta"]:

        st.info(
            "ℹ️ Milano è chiusa. "
            "Gli ETP mostrano l'ultima quotazione disponibile."
        )

    # ========================================================
    # CAMBIO EUR/USD
    # ========================================================

    cambio_eur_usd = ottieni_cambio_eur_usd()

    st.subheader(
        "💱 Cambio EUR/USD"
    )

    cambio_prezzo = cambio_eur_usd.get(
        "prezzo"
    )

    cambio_variazione = cambio_eur_usd.get(
        "variazione"
    )

    col_fx1, col_fx2 = st.columns(2)

    with col_fx1:

        if cambio_prezzo is not None:

            st.metric(
                "EUR/USD",
                f"{cambio_prezzo:.5f}",
                (
                    f"{cambio_variazione:+.2f}%"
                    if cambio_variazione is not None
                    else None
                ),
            )

        else:

            st.metric(
                "EUR/USD",
                "N/D",
            )

    with col_fx2:

        st.caption(
            "💡 Cambio utilizzato nella stima teorica "
            "per adeguare il movimento USD al prezzo EUR"
        )

    st.markdown("---")

    # ========================================================
    # RECUPERO DATI
    # ========================================================

    dati = {}

    with st.spinner(
        "Recupero dati di mercato..."
    ):

        for chiave, configurazione in TICKERS.items():

            dati[chiave] = {
                "azione": ottieni_dati_azione(
                    configurazione["azione"]
                ),
                "long": ottieni_dati_certificato(
                    configurazione["long"]
                ),
                "short": ottieni_dati_certificato(
                    configurazione["short"]
                ),
            }

    # ========================================================
    # DASHBOARD
    # ========================================================

    colonna1, colonna2 = st.columns(2)

    with colonna1:

        mostra_blocco(
            "MSTR",
            dati["MSTR"],
            stato_mercati,
            cambio_eur_usd,
            "#00b4d8",
        )

    with colonna2:

        mostra_blocco(
            "COIN",
            dati["COIN"],
            stato_mercati,
            cambio_eur_usd,
            "#ff9f1c",
        )

    # ========================================================
    # AVVERTENZA FINALE
    # ========================================================

    st.markdown("---")

    st.caption(
        "⚠️ Dati informativi: Yahoo Finance può avere ritardi; "
        "le stime 3x e di apertura sono teoriche e possono "
        "differire dal prezzo reale per cambio, spread, "
        "liquidità, NAV, costi, ribilanciamento, "
        "tracking difference, gap e condizioni di mercato. "
        "Non costituiscono una raccomandazione o consulenza "
        "di investimento."
    )


# ============================================================
# AVVIO
# ============================================================

if __name__ == "__main__":
    main()