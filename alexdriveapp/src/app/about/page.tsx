import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "О нас - AlexDrive",
  description: "AlexDrive - автомобильный дилер в Сувоне, Южная Корея",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl">
        О нас
      </h1>

      <div className="mt-8 space-y-6 text-text-secondary leading-relaxed">
        <p>
          <span className="font-semibold text-gold">AlexDrive</span> — это
          автомобильный дилер, расположенный в городе Сувон, провинция Кёнги,
          Южная Корея. Мы специализируемся на продаже подержанных автомобилей с
          автомобильных комплексов Сувона.
        </p>

        <p>
          Наша команда поможет вам подобрать идеальный автомобиль, учитывая ваши
          пожелания и бюджет. Мы предлагаем полное сопровождение сделки — от
          выбора автомобиля до оформления документов.
        </p>

        <div className="rounded-xl border border-border bg-bg-surface p-6">
          <h2 className="font-heading text-lg font-semibold text-text-primary">
            Почему мы?
          </h2>
          <ul className="mt-4 space-y-3">
            {[
              "Прямой доступ к автомобильным комплексам Сувона",
              "Проверка истории и технического состояния каждого авто",
              "Помощь с оформлением документов",
              "Консультации на русском языке",
              "Прозрачные цены без скрытых комиссий",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="mt-0.5 flex-shrink-0 text-gold"
                >
                  <path
                    d="M5 12l5 5L20 7"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
