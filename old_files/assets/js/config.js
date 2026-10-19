/*
 * Настройки сайта. Меняются без программирования.
 * Подробно — в TECH_SPEC.md.
 */
window.TMVO_CONFIG = {
  // "mock" — демо: заказы сохраняются только в браузере. "api" — заказы уходят на сервер (TECH_SPEC.md, раздел 5).
  apiMode: "mock",
  apiBase: "/api",

  shop: {
    name: "Торбеевские матрасы",
    domain: "tmvo.ru",
    phone: "8 (495) 150-30-90",
    phoneHref: "+74951503090",
    phoneNote: "Бесплатный звонок по РФ",
    messengerPhone: "+7 (985) 800-00-29",
    messengerHref: "+79858000029",
    messengers: "Viber, WhatsApp, Telegram, MAX",
    email: "info@tmvo.ru",
    hours: "Ежедневно с 10:00 до 20:00",
    workStart: "10:00",
    workEnd: "20:00",
    address: "Московская обл., Люберецкий р-н, пос. Торбеево, д. 48",
    seller: "ИП Геворгян Р. А.", // для рабочего сайта — ФИО полностью
    inn: "342102450670",
    ogrnip: "323508100652805",
    warranty: "18 месяцев"
  },

  // Способы получения. enabled:false — скрыт на сайте, код его поддерживает.
  delivery: [
    { id: "courier", title: "Доставка курьером", note: "По Москве, Московской области и регионам России. Стоимость и время согласует менеджер.", enabled: true },
    { id: "pickup",  title: "Самовывоз из шоурума", note: "пос. Торбеево, д. 48. Ежедневно с 10:00 до 20:00, по предварительному звонку.", enabled: true }
  ],

  // Способы оплаты. online:true — оплата на сайте через ЮKassa: механизм заложен, включается флагом enabled:true
  // после того, как сервер реализует /api/orders/{id}/payment (TECH_SPEC.md, раздел 9).
  payment: [
    { id: "cash",         title: "Наличными при получении", note: "Курьеру или в шоуруме",               group: "При получении",   online: false, enabled: true },
    { id: "card_courier", title: "Картой при получении",    note: "МИР, Visa, MasterCard — курьеру или в шоуруме", group: "При получении", online: false, enabled: true },
    { id: "sbp",          title: "СБП по QR-коду",          note: "Через приложение вашего банка",       group: "Онлайн",          online: true,  enabled: false },
    { id: "bank_card",    title: "Картой на сайте",         note: "МИР, Visa, MasterCard",               group: "Онлайн",          online: true,  enabled: false },
    { id: "invoice",      title: "По счёту",                note: "Для организаций",                     group: "Для организаций", online: false, enabled: false }
  ],

  // Скидки: цена со скидкой округляется вверх до 10 ₽ (как на текущем сайте).
  promoRoundTo: 10,

  // Версии текстов документов — сохраняются вместе с согласием покупателя.
  documents: {
    privacy: { title: "Политика обработки персональных данных", version: "1.0" },
    consent: { title: "Согласие на обработку персональных данных", version: "1.0" },
    offer:   { title: "Публичная оферта", version: "1.0" }
  }
};
