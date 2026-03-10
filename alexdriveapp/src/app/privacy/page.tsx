import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Политика конфиденциальности - AlexDrive",
  description: "Политика конфиденциальности AlexDrive",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <h1 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl">
        Политика конфиденциальности
      </h1>

      <div className="mt-8 space-y-8 text-text-secondary leading-relaxed">
        <p>
          Настоящая Политика конфиденциальности описывает, как{" "}
          <span className="font-semibold text-gold">AlexDrive</span> (далее —
          «мы», «нас») собирает, использует и защищает информацию, которую вы
          предоставляете при использовании нашего веб-сайта.
        </p>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            1. Какую информацию мы собираем
          </h2>
          <p className="mt-3">
            Наш сайт является каталогом автомобилей и не требует регистрации. Мы
            можем собирать следующую информацию:
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-6">
            <li>
              Техническая информация: IP-адрес, тип браузера, операционная
              система, время посещения
            </li>
            <li>
              Данные об использовании сайта: просмотренные страницы,
              взаимодействие с каталогом
            </li>
            <li>
              Контактные данные, если вы сами обращаетесь к нам через WhatsApp
              или по телефону
            </li>
          </ul>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            2. Как мы используем информацию
          </h2>
          <ul className="mt-3 list-disc space-y-1 pl-6">
            <li>Обеспечение работоспособности сайта</li>
            <li>Улучшение пользовательского опыта</li>
            <li>Обработка ваших запросов при обращении к нам</li>
            <li>Анализ посещаемости для улучшения сервиса</li>
          </ul>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            3. Хранение и защита данных
          </h2>
          <p className="mt-3">
            Мы принимаем разумные меры для защиты вашей информации. Данные
            хранятся на защищённых серверах. Мы не продаём и не передаём вашу
            личную информацию третьим лицам, за исключением случаев,
            предусмотренных законодательством.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            4. Файлы cookie
          </h2>
          <p className="mt-3">
            Сайт может использовать файлы cookie для корректной работы и анализа
            посещаемости. Вы можете отключить cookie в настройках вашего браузера.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            5. Ссылки на сторонние сайты
          </h2>
          <p className="mt-3">
            Наш сайт может содержать ссылки на сторонние ресурсы. Мы не несём
            ответственности за их политику конфиденциальности.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            6. Изменения
          </h2>
          <p className="mt-3">
            Мы оставляем за собой право обновлять данную Политику
            конфиденциальности. Изменения вступают в силу с момента публикации на
            сайте.
          </p>
        </section>

        <section>
          <h2 className="font-heading text-xl font-semibold text-text-primary">
            7. Контакты
          </h2>
          <p className="mt-3">
            Если у вас есть вопросы по данной политике, свяжитесь с нами:
          </p>
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
            href="/terms"
            className="text-sm text-gold transition-colors hover:text-gold-light"
          >
            Условия использования &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
