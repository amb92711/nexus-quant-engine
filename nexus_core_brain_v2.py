import json

class NexusCoreBrainV2:
    def __init__(self):
        self.version = "2.0 (The Casino Host Update)"
        self.laws_of_thermodynamics = []
        self._initialize_golden_rules()
        
    def _initialize_golden_rules(self):
        # 1. قانون شبانه‌روزی (Time-Agnostic Law)
        self.laws_of_thermodynamics.append(
            "THE CLOCK IS AN ILLUSION: Time of day (Asian, London, NY) does not matter for Credit Spreads. "
            "Theta decay is continuous 24/7. The only things that matter are DTE (Days to Expiration) and Strike distance."
        )
        
        # 2. قانون ضد-اسلیپیج (Strict OTM Law)
        self.laws_of_thermodynamics.append(
            "NO DEEP ITM TRAPS: Never sell an option that the current price has already crossed. "
            "For Calls, Strike MUST BE > Current Price. For Puts, Strike MUST BE < Current Price. "
            "Violating this invites extreme Bid/Ask slippage and immediate loss."
        )
        
        # 3. قانون عدم تقارن دلاری (The Premium Ratio Law) - کشف شده توسط کاربر
        self.laws_of_thermodynamics.append(
            "THE 1.5x DOLLAR ASSYMETRY: The short leg (Sell) MUST yield at least 1.5x to 2x more premium "
            "than the cost of the long leg (Buy). This guarantees that equal percentage moves result in "
            "net positive dollar outcomes (e.g., 3% profit > 3% loss)."
        )
        
        # 4. قانون حجم برابر (The Delta Balance Law)
        self.laws_of_thermodynamics.append(
            "EQUAL SIZING ONLY: To maintain a perfectly locked risk profile, the quantity of the Sell leg "
            "must exactly equal the quantity of the Buy leg (e.g., 0.1 and 0.1). Do not attempt to ratio-balance "
            "quantities manually in 0DTE spreads."
        )

    def print_core_doctrine(self):
        print(f"🧠 NEXUS-Q CORE BRAIN {self.version} 🧠\n")
        print("قوانین طلاییِ ثبت شده در هسته‌ی ماشین (غیرقابل تغییر):\n")
        for i, law in enumerate(self.laws_of_thermodynamics, 1):
            print(f"{i}. {law}\n")

if __name__ == "__main__":
    brain = NexusCoreBrainV2()
    brain.print_core_doctrine()
