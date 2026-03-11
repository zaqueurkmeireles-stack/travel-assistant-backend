from app.services.user_service import UserService
from app.services.rag_service import RAGService

us = UserService()
rag = RAGService()
TRIP = '554188368783_LISBOA_2026-04-14'
GUEST = '5541999888777'
ADMIN = '5541988368783'

# Vincular convidada com a chave correta (active_trip_id)
us.users[GUEST] = {'active_trip_id': TRIP, 'role': 'guest', 'authorized': True}
us._save_users()

active_guest = us.get_active_trip(GUEST)
active_admin = us.get_active_trip(ADMIN)
print(f'Admin viagem ativa: {active_admin}')
print(f'Convidada viagem ativa: {active_guest}')
print()

# Consulta pelo admin
r_admin = rag.query('TAP TP714 passagem Lisboa assentos', ADMIN, k=5)
print('=== ADMIN VE:')
print(r_admin[:500] if r_admin else 'NADA')
print()

# Consula pela convidada
r_guest = rag.query('TAP TP714 passagem Lisboa assentos', GUEST, k=5)
print('=== CONVIDADA VE:')
print(r_guest[:500] if r_guest else 'NADA')
print()

admin_sees_andrea = 'Andrea' in (r_admin or '')
guest_sees_zaqueu = 'Zaqueu' in (r_guest or '')
print(f'Admin ve Andrea: {admin_sees_andrea}')
print(f'Convidada ve Zaqueu: {guest_sees_zaqueu}')

docs_in_trip = [d for d in rag.documents if d['metadata'].get('trip_id') == TRIP]
print(f'Total docs na viagem: {len(docs_in_trip)}')
for d in docs_in_trip:
    fname = d['metadata'].get('filename')
    trav = d['metadata'].get('traveler')
    upld = d['metadata'].get('uploaded_by')
    print(f'  - {fname} | viajante: {trav} | upload: {upld}')
