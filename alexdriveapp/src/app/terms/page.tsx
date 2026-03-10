import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Условия использования - AlexDrive",
  description: "Условия использования сайта AlexDrive",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl">
        Условия использования
      </h1>

      <div className="mt-8 space-y-8 text-text-secondary leading-relaxed">
        <p>
          Используя сайт{" "}
          <span className="font-semibold text-gold">AlexDrive</span>, вы
          соглашаетесь с настоящими Условиями использования. Пожалуйста,
          внимательно ознакомьтесь с ними перед использованием сайта.
        </p>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            1. Общие положения
          </h2>
          <p className="mt-3">
            AlexDrive — автомобильный дилер, расположенный в городе Сувон,
            провинция Кёнги, Южная Корея. Сайт предоставляет каталог
            подержанных автомобилей, доступных на корейском рынке, а также
            справочную информацию и инструменты для расчёта стоимости.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            2. Информация на сайте
          </h2>
          <ul className="mt-3 list-disc space-y-1 pl-6">
            <li>
              Информация о транспортных средствах (цены, характеристики,
              фотографии) получена из открытых источников и может отличаться от
              актуальных данных
            </li>
            <li>
              Цены указаны в южнокорейских вонах (KRW) и носят информационный
              характер
            </li>
            <li>
              Кредитный калькулятор предоставляет приблизительные расчёты и не
              является финансовым предложением
            </li>
            <li>
              Наличие, состояние и окончательная стоимость автомобиля уточняются
              при личном обращении
            </li>
          </ul>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            3. Использование сайта
          </h2>
          <p className="mt-3">Запрещается:</p>
          <ul className="mt-3 list-disc space-y-1 pl-6">
            <li>
              Использовать сайт для незаконных целей или в нарушение
              применимого законодательства
            </li>
            <li>
              Осуществлять автоматизированный сбор данных (скрапинг) без
              предварительного письменного согласия
            </li>
            <li>
              Предпринимать попытки несанкционированного доступа к системам сайта
            </li>
            <li>
              Распространять вредоносное программное обеспечение через сайт
            </li>
          </ul>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            4. Интеллектуальная собственность
          </h2>
          <p className="mt-3">
            Все материалы, размещённые на сайте (тексты, дизайн, логотип),
            являются собственностью AlexDrive или используются с разрешения
            правообладателей. Фотографии автомобилей предоставлены площадкой
            carmanager.co.kr.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            5. Ограничение ответственности
          </h2>
          <ul className="mt-3 list-disc space-y-1 pl-6">
            <li>
              Сайт предоставляется «как есть». Мы не гарантируем бесперебойную
              или безошибочную работу
            </li>
            <li>
              AlexDrive не несёт ответственности за убытки, возникшие в
              результате использования информации с сайта
            </li>
            <li>
              Мы не несём ответственности за содержание сторонних ресурсов, на
              которые ведут ссылки с нашего сайта
            </li>
          </ul>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            6. Применимое право
          </h2>
          <p className="mt-3">
            Настоящие Условия регулируются законодательством Республики Корея.
            Все споры подлежат разрешению в судах города Сувон.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            7. Изменения условий
          </h2>
          <p className="mt-3">
            Мы оставляем за собой право обновлять настоящие Условия. Продолжая
            использовать сайт после публикации изменений, вы соглашаетесь с
            обновлёнными Условиями.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            8. Контакты
          </h2>
          <p className="mt-3">По всем вопросам обращайтесь:</p>
          <div className="mt-3 rounded-xl border border-border bg-bg-surface p-4 text-sm">
            <p className="font-medium text-text-primary">Кан Алексей</p>
            <p className="mt-1">
              Телефон:{" "}
              <a
                href="tel:+821039086050"
                className="text-gold hover:text-gold-light"
              >
                +82-10-3908-6050
              </a>
            </p>
            <p className="mt-1">
              WhatsApp:{" "}
              <a
                href="https://wa.me/821039086050"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gold hover:text-gold-light"
              >
                wa.me/821039086050
              </a>
            </p>
            <p className="mt-1">Адрес: Кёнги, Сувон, Южная Корея</p>
          </div>
        </section>

        <p className="text-xs">
          Дата последнего обновления: {new Date().toLocaleDateString("ru-RU")}
        </p>

        <div className="pt-4">
          <Link
            href="/privacy"
            className="text-sm text-gold transition-colors hover:text-gold-light"
          >
            Политика конфиденциальности &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
