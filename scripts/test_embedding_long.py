"""Does the model discriminate on chunk-length text, not just short phrases?"""

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("bhavyagiri/InLegal-Sbert")

fraud_a = (
    "The accused created a fake payment link resembling a legitimate "
    "banking portal and induced the complainant to transfer a sum of "
    "Rs. 3,00,000. The complainant discovered the deception only after "
    "the amount had been withdrawn from the account. The accused was "
    "charged under Section 420 of the Indian Penal Code for cheating "
    "and dishonestly inducing delivery of property."
)

fraud_b = (
    "The prosecution alleged that the appellant operated a fraudulent "
    "UPI collection request scheme, deceiving victims into authorising "
    "transfers under the belief that they were receiving refunds. "
    "Losses aggregating several lakhs were established. Conviction "
    "under Section 420 IPC was upheld by the High Court."
)

murder = (
    "The deceased sustained multiple incised wounds inflicted by a sharp "
    "weapon. The post-mortem report established that death occurred due "
    "to haemorrhagic shock. The Trial Court convicted the accused under "
    "Section 302 of the Indian Penal Code and sentenced him to life "
    "imprisonment, which the High Court affirmed."
)

land = (
    "The dispute concerns the boundary between two adjacent agricultural "
    "holdings. The plaintiff sought a declaration of title and permanent "
    "injunction restraining the defendant from interfering with possession. "
    "The Trial Court decreed the suit on the basis of revenue records."
)

vs = {
    n: model.encode(t)
    for n, t in [
        ("fraud_a", fraud_a),
        ("fraud_b", fraud_b),
        ("murder", murder),
        ("land", land),
    ]
}

print("SHOULD BE HIGH:")
print(
    f"  fraud_a <-> fraud_b : {util.cos_sim(vs['fraud_a'], vs['fraud_b']).item():.3f}"
)
print("\nSHOULD BE LOWER:")
for other in ("murder", "land"):
    print(
        f"  fraud_a <-> {other:8}: {util.cos_sim(vs['fraud_a'], vs[other]).item():.3f}"
    )
print(f"  murder  <-> land    : {util.cos_sim(vs['murder'], vs['land']).item():.3f}")
