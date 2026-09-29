"""Assemble the training set. REQ-7, SRS 2.6.

Two sources, because neither is sufficient alone:

1. The UCI SMS Spam Collection (5,574 real English SMS, spam and ham). Real
   human writing, which teaches the model what ordinary messages look like --
   but it is generic spam from the 2000s, with almost no UPI, KYC or
   instant-loan fraud in it.

2. A synthetic Indian financial-scam set generated here from templates. This
   covers the fraud this system actually exists to catch, and an equal volume
   of ordinary Indian messages -- bank alerts, delivery notifications, family
   chat -- so the model does not simply learn that "any message mentioning a
   bank is a scam".

SRS 2.6 states the model is trained on public datasets plus synthetic data
generated for the project, and that production-grade accuracy is not
guaranteed. This is that, done honestly: the synthetic half is clearly
labelled as synthetic, and the evaluation reports how the model does on each
source separately so the numbers cannot hide behind the easier half.
"""
import csv
import io
import random
import ssl
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
RAW = DATA / "raw"

UCI_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"

# Fixed so the dataset is reproducible: the same seed gives the same rows, and
# a model trained today can be compared with one trained next month.
SEED = 20260929

# --- synthetic Indian financial scams --------------------------------------

SCAM_TEMPLATES = [
    "URGENT: Your {bank} account will be blocked in {hours} hours. Complete KYC immediately at {link}",
    "Dear customer, your KYC has expired. Update now to avoid suspension: {link}",
    "Your {bank} debit card is deactivated. Re-activate by verifying details here {link}",
    "Congratulations! You have won Rs {amount} in the {bank} lucky draw. Claim at {link}",
    "You are selected for a cash prize of Rs {amount}. Share your UPI PIN to receive it.",
    "Refund of Rs {amount} is pending. Approve the collect request from {upi} to receive it.",
    "Payment of Rs {amount} failed. Accept the request from {upi} to get your money back.",
    "I sent Rs {amount} to your UPI by mistake. Please approve the request from {upi} and return it.",
    "Pre-approved instant loan of Rs {amount}, no documents needed. Pay processing fee to {upi}",
    "Loan approved! Pay Rs {fee} GST charges to {upi} to receive Rs {amount} within 10 minutes.",
    "Guaranteed returns of {pct}% per month. Join our premium trading group today {link}",
    "Double your money in {days} days, risk-free profit. Limited slots, last chance {link}",
    "Invest Rs {amount} in crypto and earn {pct}% daily. Guaranteed by our experts {link}",
    "Your electricity connection will be disconnected tonight. Pay pending bill at {link}",
    "Your {bank} net banking is suspended due to suspicious login. Verify OTP with our officer.",
    "This is {bank} security team. Share the OTP sent to your phone to stop the fraudulent transaction.",
    "Dear user, your PAN card is not linked to your account. Link now or account will be frozen {link}",
    "Work from home job, earn Rs {amount} daily. Pay Rs {fee} registration fee to {upi}",
    "Your parcel is held at customs. Pay Rs {fee} clearance charges at {link}",
    "Income tax refund of Rs {amount} approved. Submit bank details at {link}",
    "Your Aadhaar is linked to illegal activity. Call our officer immediately or face arrest.",
    "{bank} alert: unauthorised transaction of Rs {amount} detected. Cancel by sharing your CVV.",
    "Final notice: your credit card bill of Rs {amount} is overdue. Pay via {upi} to avoid legal action.",
    "You have an unclaimed insurance amount of Rs {amount}. Verify identity at {link}",
    "Army officer posting, need to buy your item urgently. Sending Rs {amount} via UPI request, please approve.",
    "Your Netflix subscription payment failed. Update card details within {hours} hours at {link}",
    "Get a {bank} credit card with Rs {amount} limit, no income proof. Apply {link}",
    "Your number won the KBC lottery of Rs {amount}. Pay {fee} processing to claim.",
    "SIM upgrade to 5G required. Share the OTP to complete the upgrade or service stops.",
    "Electricity bill discount scheme: pay Rs {fee} now and get Rs {amount} credit {link}",
    "Sir, I am calling from {bank}. Install this screen sharing app so I can help fix your account.",
    "Your account is under RBI investigation. Transfer funds to the safe account {upi} immediately.",
]

LEGIT_TEMPLATES = [
    "Rs {amount} debited from your {bank} account ending {last4} on {date}. Not you? Call the number on your card.",
    "Rs {amount} credited to your {bank} account ending {last4}. Available balance Rs {balance}.",
    "Your OTP is {otp}. Do not share it with anyone, including bank staff.",
    "Your {bank} statement for {month} is ready. View it in the mobile app.",
    "UPI payment of Rs {amount} to {merchant} was successful. Ref {ref}.",
    "Your order from {merchant} has been shipped and arrives on {date}.",
    "Your package was delivered today at {hour}. Thank you for shopping with {merchant}.",
    "Your {merchant} order has been cancelled and Rs {amount} will be refunded in 3-5 working days.",
    "Reminder: your electricity bill of Rs {amount} is due on {date}. Pay through the official app.",
    "Your appointment at {clinic} is confirmed for {date} at {hour}.",
    "Your train {train} is running on time. Coach {coach}, seat {seat}.",
    "Your cab is arriving in {mins} minutes. Driver {driver}, vehicle {plate}.",
    "Class test on Thursday covers chapters 4 to 6. Please bring your lab record.",
    "Hey, are we still meeting at {hour} tomorrow? Let me know if the time changed.",
    "Happy birthday! Hope you have a great day. Call me when you are free.",
    "Mummy said dinner is at {hour}, don't be late again.",
    "The assignment deadline moved to {date}. Submit on the college portal.",
    "Your {bank} credit card bill of Rs {amount} is due on {date}. Pay through the official app or net banking.",
    "Your fixed deposit of Rs {amount} matures on {date}. Visit the branch for renewal options.",
    "Your monthly SIP of Rs {amount} in {fund} has been processed.",
    "Your insurance premium of Rs {amount} is due on {date}. Renew through the official website.",
    "Your PF balance as on {date} is Rs {balance}. Check the EPFO portal for details.",
    "Interview scheduled for {date} at {hour}. Please carry two copies of your resume.",
    "Your leave request for {date} has been approved by your manager.",
    "Rent for {month} received, Rs {amount}. Receipt will be shared by email.",
    "Your gas cylinder booking is confirmed. Delivery expected on {date}.",
    "Thanks for your payment of Rs {amount}. Your subscription is active until {date}.",
    "Your flight {flight} is delayed by {mins} minutes. New departure {hour}.",
    "Water supply will be interrupted on {date} from {hour} for maintenance work.",
    "Society meeting on {date} at {hour} in the community hall. Please attend.",
    "Your test results are ready for collection at {clinic} reception.",
    "Reminder: library book due on {date}. Renew online to avoid a fine.",
]

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak", "PNB", "Canara Bank",
         "Bank of Baroda", "Yes Bank", "IndusInd"]
UPIS = ["fraudster@ybl", "quickpay@okaxis", "refund.help@oksbi", "support123@paytm",
        "kycverify@okhdfcbank", "instantloan@upi", "winner.claim@ybl", "safeaccount@okicici"]
LINKS = ["http://bit.ly/kyc-verify", "http://tinyurl.com/sbi-update", "https://sbi-kyc.online",
         "http://rb.gy/claim-now", "https://hdfc-secure.xyz", "http://is.gd/loan-approve",
         "https://icici-verify.co", "http://t.me/investgroup"]
MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "Zomato", "Myntra", "BigBasket", "Blinkit", "Nykaa"]
CLINICS = ["Apollo Clinic", "Manipal Hospital", "Fortis", "the city health centre"]
FUNDS = ["Axis Bluechip Fund", "HDFC Index Fund", "SBI Small Cap", "Parag Parikh Flexi Cap"]
DRIVERS = ["Ramesh", "Suresh", "Anil", "Vijay", "Imran", "Karthik"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def fill(template: str, rng: random.Random) -> str:
    return template.format(
        bank=rng.choice(BANKS),
        upi=rng.choice(UPIS),
        link=rng.choice(LINKS),
        merchant=rng.choice(MERCHANTS),
        clinic=rng.choice(CLINICS),
        fund=rng.choice(FUNDS),
        driver=rng.choice(DRIVERS),
        month=rng.choice(MONTHS),
        amount=f"{rng.choice([500, 1999, 4999, 10000, 25000, 50000, 99999, 150000]):,}",
        balance=f"{rng.randint(1000, 250000):,}",
        fee=rng.choice([99, 199, 499, 999, 1500]),
        pct=rng.choice([5, 10, 15, 20, 30, 50]),
        days=rng.choice([7, 15, 30, 45]),
        hours=rng.choice([2, 6, 12, 24, 48]),
        mins=rng.choice([5, 10, 15, 30, 45]),
        last4=rng.randint(1000, 9999),
        otp=rng.randint(100000, 999999),
        ref=rng.randint(10**11, 10**12 - 1),
        date=f"{rng.randint(1, 28)} {rng.choice(MONTHS)}",
        hour=f"{rng.randint(1, 12)}:{rng.choice(['00', '15', '30', '45'])} {rng.choice(['am', 'pm'])}",
        train=rng.randint(10000, 19999),
        coach=f"S{rng.randint(1, 12)}",
        seat=rng.randint(1, 72),
        plate=f"KA{rng.randint(10, 99)}{rng.choice('ABCDEFGHJKLMNP')}{rng.randint(1000, 9999)}",
        flight=f"{rng.choice(['6E', 'AI', 'UK', 'SG'])}{rng.randint(100, 999)}",
    )


def _vary(text: str, rng: random.Random) -> str:
    """Small surface noise, so the model cannot key on template punctuation.

    Real scam messages are riddled with shouting, odd spacing and missing
    punctuation; training on perfectly clean templates would teach the model
    that tidy text is safe.
    """
    if rng.random() < 0.15:
        text = text.upper()
    if rng.random() < 0.20:
        text = text.replace(".", "")
    if rng.random() < 0.15:
        text = text.replace(" ", "  ", 1)
    if rng.random() < 0.10:
        text = text + rng.choice([" Reply STOP to opt out", " -Team", " !!", " Act now"])
    return text


def build_synthetic(per_class: int = 700) -> list[tuple[str, int, str]]:
    rng = random.Random(SEED)
    rows: list[tuple[str, int, str]] = []
    seen: set[str] = set()

    for label, templates in ((1, SCAM_TEMPLATES), (0, LEGIT_TEMPLATES)):
        made = 0
        attempts = 0
        # Duplicates would inflate the scores by leaking identical rows across
        # the train/test split, so only unique messages are kept.
        while made < per_class and attempts < per_class * 60:
            attempts += 1
            text = _vary(fill(rng.choice(templates), rng), rng)
            if text in seen:
                continue
            seen.add(text)
            rows.append((text, label, "synthetic_in"))
            made += 1
    return rows


# --- public dataset ---------------------------------------------------------


def fetch_uci() -> list[tuple[str, int, str]]:
    RAW.mkdir(parents=True, exist_ok=True)
    archive = RAW / "sms_spam_collection.zip"

    if not archive.exists():
        print(f"downloading {UCI_URL}")
        # The UCI host presents a chain some Windows Python builds reject; this
        # download is a public, checksum-free corpus, so an unverified fetch is
        # acceptable here and nowhere else in this project.
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(UCI_URL, context=context, timeout=90) as response:
            archive.write_bytes(response.read())
    print(f"using {archive} ({archive.stat().st_size:,} bytes)")

    rows: list[tuple[str, int, str]] = []
    with zipfile.ZipFile(archive) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith("smsspamcollection"))
        raw = zf.read(name).decode("latin-1")

    for line in io.StringIO(raw):
        line = line.strip()
        if not line or "\t" not in line:
            continue
        label, text = line.split("\t", 1)
        rows.append((text, 1 if label.strip().lower() == "spam" else 0, "uci_sms"))
    return rows


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    synthetic = build_synthetic()
    out_synth = DATA / "synthetic_in.csv"
    with out_synth.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["text", "label", "source"])
        writer.writerows(synthetic)
    print(f"synthetic: {len(synthetic):,} rows -> {out_synth.name}")

    uci = fetch_uci()
    print(f"uci_sms:   {len(uci):,} rows")

    combined = synthetic + uci
    out = DATA / "train.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["text", "label", "source"])
        writer.writerows(combined)

    scams = sum(1 for _, label, _ in combined if label == 1)
    print(f"combined:  {len(combined):,} rows -> {out.name}")
    print(f"           {scams:,} scam / {len(combined) - scams:,} legitimate")


if __name__ == "__main__":
    main()
