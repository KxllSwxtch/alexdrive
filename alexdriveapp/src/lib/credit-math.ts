export interface CalculatorInput {
  carPrice: number;     // = loan/financing amount (carnoon's 원금)
  termMonths: number;
  annualRate: number;
}

export interface MonthlyRow {
  month: number;
  principalPaid: number;
  interestPaid: number;
  payment: number;
  remainingBalance: number;
}

export interface CalculationResult {
  loanAmount: number;
  schedule: MonthlyRow[];
  totalInterest: number;
  totalPayment: number;
  monthlyPayment: number;
}

export function validateInputs(input: CalculatorInput): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  if (input.carPrice <= 0) errors.push("Сумма кредита должна быть больше 0");
  if (input.annualRate < 0 || input.annualRate > 100)
    errors.push("Процентная ставка должна быть от 0 до 100");
  if (input.termMonths <= 0) errors.push("Срок кредита должен быть больше 0");
  return { valid: errors.length === 0, errors };
}

export function calculateCredit(
  input: CalculatorInput
): CalculationResult | null {
  const { valid } = validateInputs(input);
  if (!valid) return null;

  const loanAmount = input.carPrice;

  const n = input.termMonths;
  const monthlyRate = input.annualRate / 100 / 12;
  const schedule: MonthlyRow[] = [];
  let remaining = loanAmount;

  let payment: number;
  if (monthlyRate === 0) {
    payment = Math.floor(loanAmount / n);
  } else {
    const factor = Math.pow(1 + monthlyRate, n);
    payment = Math.floor((loanAmount * monthlyRate * factor) / (factor - 1));
  }

  for (let i = 1; i <= n; i++) {
    let interest: number;
    let principal: number;
    let monthPayment: number;

    if (i === n) {
      principal = remaining;
      interest = payment - principal;
      monthPayment = payment;
    } else {
      interest = Math.round(remaining * monthlyRate);
      principal = payment - interest;
      monthPayment = payment;
    }

    remaining -= principal;

    schedule.push({
      month: i,
      principalPaid: principal,
      interestPaid: interest,
      payment: monthPayment,
      remainingBalance: Math.max(remaining, 0),
    });
  }

  const totalInterest = schedule.reduce((s, r) => s + r.interestPaid, 0);
  const totalPayment = schedule.reduce((s, r) => s + r.payment, 0);

  return {
    loanAmount,
    schedule,
    totalInterest,
    totalPayment,
    monthlyPayment: schedule[0].payment,
  };
}
