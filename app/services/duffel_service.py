"""
Duffel Service - Busca e reserva de voos via REST API direta (sem SDK)
Suporta: busca multi-passageiro, múltiplos resultados, booking real.
"""

import requests
from app.config import settings
from loguru import logger
from typing import List, Dict, Optional

DUFFEL_BASE_URL = "https://api.duffel.com/air"

class DuffelService:
    """Service para integração com Duffel via REST API (sem SDK)"""

    def __init__(self):
        self.api_key = settings.DUFFEL_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Duffel-Version": "v2",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            logger.info("✅ Duffel Service inicializado (REST direto)")
        else:
            logger.warning("⚠️ Chave do Duffel não configurada.")

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        cabin_class: str = "economy"
    ) -> str:
        """
        Busca as melhores ofertas de voos reais via Duffel.
        origin/destination: Códigos IATA (ex: GRU, LIS)
        departure_date / return_date: YYYY-MM-DD
        adults / children: quantidade de passageiros
        """
        if not self.api_key:
            return "Duffel não configurado. Adicione DUFFEL_API_KEY no ambiente."

        # Montar passageiros
        passengers = [{"type": "adult"} for _ in range(adults)]
        passengers += [{"type": "child"} for _ in range(children)]

        # Montar trechos
        slices = [{"origin": origin, "destination": destination, "departure_date": departure_date}]
        if return_date:
            slices.append({"origin": destination, "destination": origin, "departure_date": return_date})

        payload = {
            "data": {
                "slices": slices,
                "passengers": passengers,
                "cabin_class": cabin_class,
            }
        }

        try:
            logger.info(f"✈️ Buscando voos Duffel: {origin} -> {destination} | {adults}A+{children}C | {departure_date}")
            resp = requests.post(
                f"{DUFFEL_BASE_URL}/offer_requests?return_offers=true",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                logger.error(f"Duffel erro {resp.status_code}: {resp.text[:300]}")
                return f"Erro na busca de voos (código {resp.status_code}). Tente novamente."

            data = resp.json().get("data", {})
            offers = data.get("offers", [])

            if not offers:
                return f"Nenhum voo encontrado de {origin} para {destination} na data {departure_date}."

            # Ordenar pelo preço total (mais barato primeiro)
            offers_sorted = sorted(offers, key=lambda o: float(o.get("total_amount", 99999)))

            # Formatar as top 5 ofertas
            pax_label = f"{adults} adulto(s)" + (f" + {children} criança(s)" if children > 0 else "")
            result = f"✈️ *MELHORES VOOS: {origin} → {destination}*\n"
            result += f"📅 Ida: {departure_date}"
            if return_date:
                result += f" | Volta: {return_date}"
            result += f" | {pax_label}\n\n"

            for i, offer in enumerate(offers_sorted[:5], 1):
                amount = float(offer.get("total_amount", 0))
                currency = offer.get("total_currency", "USD")
                airline = offer.get("owner", {}).get("name", "Cia desconhecida")
                offer_id = offer.get("id", "")
                stops = 0

                # Detalhes do primeiro trecho
                first_slice = offer.get("slices", [{}])[0]
                segments = first_slice.get("segments", [])
                dep_at = segments[0].get("departing_at", "")[:16].replace("T", " ") if segments else ""
                arr_at = segments[-1].get("arriving_at", "")[:16].replace("T", " ") if segments else ""
                stops = len(segments) - 1
                duration_min = first_slice.get("duration", "")

                result += f"*{i}. {airline}*\n"
                result += f"   💰 {amount:.2f} {currency} ({pax_label})\n"
                result += f"   🛫 Saída: {dep_at}\n"
                result += f"   🛬 Chegada: {arr_at}\n"
                result += f"   🔗 Paradas: {'Direto' if stops == 0 else f'{stops} conexão(ões)'}\n"
                result += f"   🆔 ID: `{offer_id[:30]}...`\n\n"

            result += "_Para reservar a opção desejada, me diga o número (1-5) ou o ID da oferta!_"
            return result

        except Exception as e:
            logger.error(f"Erro Duffel search_flights: {e}")
            return f"Falha ao buscar voos: {str(e)}"

    def get_offer_details(self, offer_id: str) -> dict:
        """Retorna detalhes completos de uma oferta para booking"""
        try:
            resp = requests.get(
                f"{DUFFEL_BASE_URL}/offers/{offer_id}",
                headers=self.headers,
                timeout=15,
            )
            return resp.json().get("data", {})
        except Exception as e:
            logger.error(f"Erro ao buscar oferta {offer_id}: {e}")
            return {}

    def create_order(
        self,
        offer_id: str,
        passenger_name: str,
        passenger_email: str,
        birth_date: str,
        phone: str = "",
    ) -> str:
        """
        Reserva uma passagem (requer chave duffel_live_ para produção).
        birth_date: YYYY-MM-DD
        """
        if not self.api_key:
            return "Duffel não configurado."

        if "duffel_test" in self.api_key:
            logger.warning("⚠️ Usando chave de TESTE — reserva não é real.")

        # Separar nome
        parts = passenger_name.strip().split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else "."

        payload = {
            "data": {
                "type": "instant",
                "selected_offers": [offer_id],
                "passengers": [
                    {
                        "id": "pas_0",  # deve ser preenchido com o ID real do passageiro da oferta
                        "born_on": birth_date,
                        "title": "mr",
                        "gender": "m",
                        "given_name": first,
                        "family_name": last,
                        "email": passenger_email,
                        "phone_number": phone or "+5511999999999",
                    }
                ],
                "payments": [
                    {
                        "type": "balance",
                        "currency": "USD",
                        "amount": "0",  # Duffel debita automaticamente do saldo
                    }
                ],
            }
        }

        try:
            logger.info(f"🎫 Criando reserva Duffel para oferta {offer_id[:30]}...")
            resp = requests.post(
                f"{DUFFEL_BASE_URL}/orders",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                order = resp.json().get("data", {})
                booking_ref = order.get("booking_reference", "N/A")
                return (
                    f"✅ *RESERVA CONFIRMADA!*\n\n"
                    f"📋 Referência: *{booking_ref}*\n"
                    f"👤 Passageiro: {passenger_name}\n"
                    f"📧 Confirmação enviada para: {passenger_email}\n\n"
                    f"_Guarde o código de reserva: {booking_ref}_"
                )
            else:
                err = resp.json()
                logger.error(f"Erro booking Duffel: {err}")
                return f"Erro ao reservar (code {resp.status_code}): {err.get('errors', [{}])[0].get('message', 'Erro desconhecido')}"

        except Exception as e:
            logger.error(f"Erro Duffel create_order: {e}")
            return f"Falha ao criar reserva: {str(e)}"
