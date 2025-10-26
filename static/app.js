const { useState, useCallback, useRef, useEffect } = React;

const DonEstateApp = () => {
  const [currentScreen, setCurrentScreen] = useState("main");
  const [modal, setModal] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);

  // Search form state
  const [searchForm, setSearchForm] = useState({
    transactionType: "",
    propertyTypes: [],
    rooms: "",
    district: "",
    budgetMin: "",
    budgetMax: "",
    requirements: "",
    name: "",
    phone: "",
  });

  // Offer form state
  const [offerForm, setOfferForm] = useState({
    transactionType: "",
    propertyType: "",
    address: "",
    area: "",
    floors: "",
    rooms: "",
    price: "",
    description: "",
    name: "",
    phone: "",
    photos: [],
    video: null,
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [mapProperties, setMapProperties] = useState([]);
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const [searchProgress, setSearchProgress] = useState(0);
  const [offerProgress, setOfferProgress] = useState(0);

  const ProgressBar = ({ progress }) => (
    <div className="progress-bar-container">
      <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      <div className="progress-text">{Math.round(progress)}%</div>
    </div>
  );

  useEffect(() => {
    // Dynamically load Yandex Maps API
    const fetchConfigAndLoadMap = async () => {
      try {
        const response = await fetch("/api/config/");
        const config = await response.json();
        setIsAdmin(config.is_admin);
        const script = document.createElement("script");
        script.src = `https://api-maps.yandex.ru/2.1/?apikey=${config.yandex_maps_api_key}&lang=ru_RU`;
        script.async = true;
        document.head.appendChild(script);
      } catch (error) {
        console.error("Failed to load map config:", error);
      }
    };

    fetchConfigAndLoadMap();
  }, []);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;

      const applyTheme = () => {
        if (tg.colorScheme === "dark") {
          document.documentElement.setAttribute("data-color-scheme", "dark");
        } else {
          document.documentElement.setAttribute("data-color-scheme", "light");
        }
      };

      tg.onEvent("themeChanged", applyTheme);
      applyTheme(); // Apply theme on initial load
      return () => {
        tg.offEvent("themeChanged", applyTheme);
      };
    }
  }, []);

  useEffect(() => {
    try {
      const savedSearchForm = localStorage.getItem("don_estate_search_form");
      if (savedSearchForm) {
        setSearchForm(JSON.parse(savedSearchForm));
      }
      const savedOfferForm = localStorage.getItem("don_estate_offer_form");
      if (savedOfferForm) {
        const parsedOfferForm = JSON.parse(savedOfferForm);
        delete parsedOfferForm.photos;
        delete parsedOfferForm.video;
        setOfferForm((prev) => ({ ...prev, ...parsedOfferForm }));
      }
    } catch (error) {
      console.error("Failed to load form data from localStorage", error);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(
        "don_estate_search_form",
        JSON.stringify(searchForm),
      );
    } catch (error) {
      console.error("Failed to save search form data to localStorage", error);
    }
  }, [searchForm]);

  useEffect(() => {
    try {
      const { photos, video, ...formDataToSave } = offerForm;
      localStorage.setItem(
        "don_estate_offer_form",
        JSON.stringify(formDataToSave),
      );
    } catch (error) {
      console.error("Failed to save offer form data to localStorage", error);
    }
  }, [offerForm]);

  useEffect(() => {
    const requiredFields = [
      "transactionType",
      "propertyTypes",
      "name",
      "phone",
    ];
    const filledFields = requiredFields.filter((field) => {
      const value = searchForm[field];
      return Array.isArray(value) ? value.length > 0 : !!value;
    }).length;
    setSearchProgress((filledFields / requiredFields.length) * 100);
  }, [searchForm]);

  useEffect(() => {
    const requiredFields = [
      "transactionType",
      "propertyType",
      "address",
      "name",
      "phone",
    ];
    const filledFields = requiredFields.filter(
      (field) => !!offerForm[field],
    ).length;
    setOfferProgress((filledFields / requiredFields.length) * 100);
  }, [offerForm]);

  const validatePhone = (phone) =>
    /^[+]?[0-9]{10,15}$/.test(phone.replace(/[\s\-()]/g, ""));

  const validateField = (form, name, value) => {
    const currentForm = form === "search" ? searchForm : offerForm;
    switch (name) {
      case "transactionType":
        return !value ? "Выберите тип сделки" : null;
      case "propertyTypes":
        return value.length === 0
          ? "Выберите хотя бы один тип недвижимости"
          : null;
      case "name":
        return !value.trim() ? "Введите ваше имя" : null;
      case "phone":
        if (!value.trim()) return "Введите номер телефона";
        if (!validatePhone(value)) return "Введите корректный номер телефона";
        return null;
      case "budgetMax":
        if (
          currentForm.budgetMin &&
          value &&
          parseFloat(value) <= parseFloat(currentForm.budgetMin)
        ) {
          return "Максимальная сумма должна быть больше минимальной";
        }
        return null;
      case "propertyType":
        return !value ? "Выберите тип недвижимости" : null;
      case "address":
        return !value.trim() ? "Введите адрес" : null;
      default:
        return null;
    }
  };

  const handleBlur = (form) => (e) => {
    const { name, value } = e.target;
    const error = validateField(form, name, value);
    setErrors((prev) => ({ ...prev, [name]: error }));
  };

  const validateSearchForm = () => {
    const fieldsToValidate = [
      "transactionType",
      "propertyTypes",
      "name",
      "phone",
      "budgetMax",
    ];
    const newErrors = {};
    fieldsToValidate.forEach((field) => {
      const error = validateField("search", field, searchForm[field]);
      if (error) newErrors[field] = error;
    });
    return newErrors;
  };

  const validateOfferForm = () => {
    const fieldsToValidate = [
      "transactionType",
      "propertyType",
      "address",
      "name",
      "phone",
    ];
    const newErrors = {};
    fieldsToValidate.forEach((field) => {
      const error = validateField("offer", field, offerForm[field]);
      if (error) newErrors[field] = error;
    });
    return newErrors;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${["Bytes", "KB", "MB", "GB"][i]}`;
  };

  const handleFileUpload = (files, type) => {
    const fileArray = Array.from(files);
    if (type === "photos") {
      const validFiles = fileArray.filter(
        (file) =>
          ["image/jpeg", "image/png", "image/webp"].includes(file.type) &&
          file.size <= 5 * 1024 * 1024,
      );
      if (offerForm.photos.length + validFiles.length > 10) {
        setModal({ type: "error", message: "Максимум 10 фотографий" });
        return;
      }
      setOfferForm((prev) => ({
        ...prev,
        photos: [...prev.photos, ...validFiles],
      }));
    } else if (type === "video") {
      const file = fileArray[0];
      if (
        !["video/mp4", "video/mov"].includes(file.type) ||
        file.size > 50 * 1024 * 1024
      ) {
        setModal({
          type: "error",
          message: "Видео должно быть MP4/MOV и до 50МБ",
        });
        return;
      }
      setOfferForm((prev) => ({ ...prev, video: file }));
    }
  };

  const removePhoto = (index) =>
    setOfferForm((prev) => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index),
    }));
  const removeVideo = () => setOfferForm((prev) => ({ ...prev, video: null }));

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add("dragover");
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove("dragover");
  };
  const handleDrop = (e, type) => {
    e.preventDefault();
    e.currentTarget.classList.remove("dragover");
    handleFileUpload(e.dataTransfer.files, type);
  };

  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateSearchForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    setIsLoading(true);
    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-telegram-user-id": tg.initDataUnsafe?.user?.id || "0",
        },
        body: JSON.stringify({
          transaction_type:
            searchForm.transactionType === "Купить" ? "sell" : "rent",
          property_types: searchForm.propertyTypes.map((p) => p.toLowerCase()),
          rooms: searchForm.rooms ? parseInt(searchForm.rooms) : undefined,
          district: searchForm.district,
          budget_min: searchForm.budgetMin
            ? parseFloat(searchForm.budgetMin)
            : undefined,
          budget_max: searchForm.budgetMax
            ? parseFloat(searchForm.budgetMax)
            : undefined,
          query_text: searchForm.requirements,
        }),
      });
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setSearchResults(data.results);
      setCurrentScreen("results");
    } catch (error) {
      console.error("Failed to fetch search results:", error);
      setModal({
        type: "error",
        message: "Не удалось выполнить поиск. Попробуйте еще раз.",
      });
    } finally {
      setIsSubmitting(false);
      setIsLoading(false);
    }
  };

  const handleOfferSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateOfferForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      const { photos, video, ...formData } = offerForm;
      const response = await fetch("/api/offers/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error("Failed to submit offer");
      setModal({ type: "success", message: "✅ Заявка успешно отправлена!" });
      setTimeout(() => {
        setOfferForm({
          transactionType: "",
          propertyType: "",
          address: "",
          area: "",
          floors: "",
          rooms: "",
          price: "",
          description: "",
          name: "",
          phone: "",
          photos: [],
          video: null,
        });
        localStorage.removeItem("don_estate_offer_form");
        setModal(null);
        setCurrentScreen("main");
      }, 2000);
    } catch (error) {
      console.error(error);
      setModal({ type: "error", message: "Не удалось отправить заявку." });
    } finally {
      setIsSubmitting(false);
    }
  };

  const fetchFavorites = async () => {
    setIsLoading(true);
    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch("/api/favorites/", {
        headers: { "x-telegram-user-id": tg.initDataUnsafe?.user?.id || "0" },
      });
      if (!response.ok) throw new Error("Failed to fetch favorites");
      const data = await response.json();
      setFavorites(data);
    } catch (error) {
      console.error(error);
      setModal({ type: "error", message: "Не удалось загрузить избранное." });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFavorite = async (propertyId, isFavorite) => {
    try {
      const tg = window.Telegram.WebApp;
      const method = isFavorite ? "POST" : "DELETE";
      const url = isFavorite
        ? "/api/favorites/"
        : `/api/favorites/${propertyId}`;
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "x-telegram-user-id": tg.initDataUnsafe?.user?.id || "0",
        },
        body: isFavorite ? JSON.stringify({ property_id: propertyId }) : null,
      });
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const updateProperty = (p) =>
        p.id === propertyId ? { ...p, is_favorite: isFavorite } : p;
      setSearchResults((prev) => prev.map(updateProperty));
      if (isFavorite) {
        const propToAdd = searchResults.find((p) => p.id === propertyId);
        if (propToAdd)
          setFavorites((prev) => [
            ...prev,
            { ...propToAdd, is_favorite: true },
          ]);
      } else {
        setFavorites((prev) => prev.filter((p) => p.id !== propertyId));
      }
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
      setModal({ type: "error", message: "Не удалось обновить избранное." });
    }
  };

  const handlePropertyTypeChange = (type, checked) => {
    setSearchForm((prev) => ({
      ...prev,
      propertyTypes: checked
        ? [...prev.propertyTypes, type]
        : prev.propertyTypes.filter((t) => t !== type),
    }));
  };

  const MainScreen = () => (
    <div className="screen">
      <div className="container">
        <div className="header">
          <img
            src="/static/assets/logo.jpg"
            alt="Don Estate"
            className="logo"
          />
          <p>Агентство недвижимости в Донецке</p>
        </div>
        <div className="main-buttons">
          <button
            className="btn btn-primary"
            onClick={() => setCurrentScreen("search")}
          >
            🔍 Найти недвижимость
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen("offer")}
          >
            🏠 Предложить объект
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen("favorites")}
          >
            ❤️ Избранное
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen("map")}
          >
            🗺️ Карта
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setCurrentScreen("chat")}
          >
            💬 Чат с ассистентом
          </button>
        </div>
      </div>
    </div>
  );

  const SkeletonCard = () => (
    <div className="property-card skeleton">
      <div className="property-card__image-container skeleton-anim"></div>
      <div className="property-card__content">
        <div className="skeleton-text skeleton-anim"></div>
        <div className="skeleton-text short skeleton-anim"></div>
        <div className="skeleton-text long skeleton-anim"></div>
      </div>
    </div>
  );

  const EmptyState = ({ icon, title, message }) => (
    <div className="empty-state">
      <div className="empty-state__icon">{icon}</div>
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__message">{message}</p>
    </div>
  );

  const PropertyCard = ({ property, onToggleFavorite }) => (
    <div className="property-card">
      <div className="property-card__image-container">
        {property.photos && property.photos.length > 0 ? (
          <img
            src={property.photos[0]}
            alt={property.title}
            className="property-card__image"
          />
        ) : (
          <div className="property-card__no-image">Нет фото</div>
        )}
        <button
          className={`property-card__favorite-btn ${property.is_favorite ? "active" : ""}`}
          onClick={() => onToggleFavorite(property.id, !property.is_favorite)}
        >
          ❤️
        </button>
      </div>
      <div className="property-card__content">
        <h3 className="property-card__title">{property.title}</h3>
        <p className="property-card__price">
          {property.price_usd
            ? `$${property.price_usd.toLocaleString()}`
            : "Цена не указана"}
        </p>
        <p className="property-card__address">
          {property.address || "Адрес не указан"}
        </p>
        <p className="property-card__description">{property.description}</p>
      </div>
    </div>
  );

  const ResultsScreen = ({
    results,
    onToggleFavorite,
    searchCriteria,
    isLoading,
  }) => {
    const handleSaveSearch = async () => {
      try {
        const tg = window.Telegram.WebApp;
        const response = await fetch("/api/searches/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-telegram-user-id": tg.initDataUnsafe?.user?.id || "0",
          },
          body: JSON.stringify({ criteria: searchCriteria }),
        });
        if (!response.ok) throw new Error("Failed to save search");
        setModal({
          type: "success",
          message:
            "✅ Поиск сохранен! Мы будем уведомлять вас о новых объектах.",
        });
        setTimeout(() => setModal(null), 2000);
      } catch (error) {
        console.error(error);
        setModal({ type: "error", message: "Не удалось сохранить поиск." });
      }
    };
    return (
      <div className="screen">
        <div className="container">
          <button
            className="btn btn-back"
            onClick={() => setCurrentScreen("search")}
          >
            ◀ Назад к поиску
          </button>
          <div className="header">
            <h1>Результаты поиска</h1>
            <button className="btn btn-secondary" onClick={handleSaveSearch}>
              💾 Сохранить поиск
            </button>
          </div>
          <div className="results-list">
            {isLoading ? (
              [...Array(3)].map((_, i) => <SkeletonCard key={i} />)
            ) : results.length > 0 ? (
              results.map((prop) => (
                <PropertyCard
                  key={prop.id}
                  property={prop}
                  onToggleFavorite={onToggleFavorite}
                />
              ))
            ) : (
              <EmptyState
                icon="🤷"
                title="Ничего не найдено"
                message="Попробуйте изменить критерии поиска или расширить бюджет."
              />
            )}
          </div>
        </div>
      </div>
    );
  };

  const FavoritesScreen = ({ favorites, onToggleFavorite, isLoading }) => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen("main")}
        >
          ◀ Назад
        </button>
        <div className="header">
          <h1>Избранное</h1>
        </div>
        <div className="results-list">
          {isLoading ? (
            [...Array(3)].map((_, i) => <SkeletonCard key={i} />)
          ) : favorites.length > 0 ? (
            favorites.map((prop) => (
              <PropertyCard
                key={prop.id}
                property={prop}
                onToggleFavorite={onToggleFavorite}
              />
            ))
          ) : (
            <EmptyState
              icon="❤️"
              title="Список избранного пуст"
              message="Нажимайте на сердечко в карточках объектов, чтобы добавлять их сюда."
            />
          )}
        </div>
      </div>
    </div>
  );

  const MapScreen = () => {
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const handleMyLocation = () => {
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.requestLocation((loc) => {
          if (mapInstance.current) {
            const userCoords = [loc.latitude, loc.longitude];
            mapInstance.current.setCenter(userCoords, 14);
            const userPlacemark = new ymaps.Placemark(
              userCoords,
              { hintContent: "Вы здесь" },
              { preset: "islands#geolocationIcon", iconColor: "#ff0000" },
            );
            mapInstance.current.geoObjects.add(userPlacemark);
          }
        });
      }
    };
    useEffect(() => {
      const initMap = () => {
        if (!mapRef.current) return;
        mapInstance.current = new ymaps.Map(mapRef.current, {
          center: [48.015, 37.802],
          zoom: 12,
        });
        fetchMapProperties(mapInstance.current);
      };
      ymaps.ready(initMap);
    }, []);
    const fetchMapProperties = async (map) => {
      try {
        const response = await fetch("/api/map/properties");
        if (!response.ok) throw new Error("Failed to fetch map properties");
        const properties = await response.json();
        setMapProperties(properties);
        properties.forEach((prop) => {
          const placemark = new ymaps.Placemark(
            [prop.latitude, prop.longitude],
            {
              balloonContentHeader: prop.title,
              balloonContentBody: `$${prop.price_usd.toLocaleString()}`,
              hintContent: prop.title,
            },
          );
          map.geoObjects.add(placemark);
        });
      } catch (error) {
        console.error(error);
        setModal({
          type: "error",
          message: "Не удалось загрузить объекты на карте.",
        });
      }
    };
    return (
      <div className="screen map-screen">
        <div
          id="map"
          ref={mapRef}
          style={{ width: "100%", height: "100%" }}
        ></div>
        <button
          className="btn btn-back map-back-btn"
          onClick={() => setCurrentScreen("main")}
        >
          ◀ Назад
        </button>
        <button
          className="btn btn-primary map-location-btn"
          onClick={handleMyLocation}
        >
          📍 Мое местоположение
        </button>
      </div>
    );
  };

  const ChatScreen = () => {
    const [messages, setMessages] = useState([
      { sender: "bot", text: "Здравствуйте! Чем могу помочь?" },
    ]);
    const [inputValue, setInputValue] = useState("");
    const [isBotTyping, setIsBotTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const scrollToBottom = () =>
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(scrollToBottom, [messages]);
    const handleSendMessage = async (e) => {
      e.preventDefault();
      if (!inputValue.trim()) return;
      const userMessage = { sender: "user", text: inputValue };
      setMessages((prev) => [...prev, userMessage]);
      setInputValue("");
      setIsBotTyping(true);
      try {
        const response = await fetch("/api/chat/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: inputValue }),
        });
        if (!response.ok) throw new Error("Failed to get response from bot");
        const botResponse = await response.json();
        let botMessage = {
          sender: "bot",
          text: "Извините, я не смог обработать ваш запрос.",
        };
        if (botResponse.type === "text") botMessage.text = botResponse.content;
        else if (botResponse.type === "property_list") {
          botMessage.text = botResponse.summary;
          botMessage.properties = botResponse.properties;
        }
        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        console.error(error);
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: "Произошла ошибка. Попробуйте еще раз." },
        ]);
      } finally {
        setIsBotTyping(false);
      }
    };
    return (
      <div className="screen chat-screen">
        <div className="chat-header">
          <button
            className="btn btn-back"
            onClick={() => setCurrentScreen("main")}
          >
            ◀
          </button>
          <h1>AI Ассистент</h1>
        </div>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              <p>{msg.text}</p>
              {msg.properties && (
                <div className="chat-property-cards">
                  {msg.properties.map((prop) => (
                    <div key={prop.id} className="chat-property-card">
                      {prop.photo_url && <img src={prop.photo_url} />}
                      <div className="chat-property-card-info">
                        <b>{prop.title}</b>
                        <p>{prop.address}</p>
                        <p>${prop.price_usd?.toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {isBotTyping && <div className="chat-bubble bot typing">...</div>}
          <div ref={messagesEndRef} />
        </div>
        <form className="chat-input-form" onSubmit={handleSendMessage}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Спросите что-нибудь..."
            disabled={isBotTyping}
          />
          <button type="submit" disabled={isBotTyping}>
            ➤
          </button>
        </form>
      </div>
    );
  };

  const SearchScreen = () => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen("main")}
        >
          ◀ Назад
        </button>
        <div className="header">
          <h1>Найти недвижимость</h1>
        </div>
        <form className="form" onSubmit={handleSearchSubmit}>
          <ProgressBar progress={searchProgress} />
          <div className="form-group">
            <label className="form-label">
              Тип сделки <span className="required">*</span>
            </label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Купить"
                  checked={searchForm.transactionType === "Купить"}
                  onChange={(e) => {
                    setSearchForm((prev) => ({
                      ...prev,
                      transactionType: e.target.value,
                    }));
                    setErrors((prev) => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur("search")}
                />
                Купить
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Снять"
                  checked={searchForm.transactionType === "Снять"}
                  onChange={(e) => {
                    setSearchForm((prev) => ({
                      ...prev,
                      transactionType: e.target.value,
                    }));
                    setErrors((prev) => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur("search")}
                />
                Снять
              </label>
            </div>
            {errors.transactionType && (
              <div className="error-message">{errors.transactionType}</div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">
              Тип недвижимости <span className="required">*</span>
            </label>
            <div className="checkbox-group">
              {["Квартира", "Дом", "Коммерческая недвижимость"].map((type) => (
                <label key={type} className="checkbox-option">
                  <input
                    type="checkbox"
                    name="propertyTypes"
                    checked={searchForm.propertyTypes.includes(type)}
                    onChange={(e) => {
                      handlePropertyTypeChange(type, e.target.checked);
                      setErrors((prev) => ({ ...prev, propertyTypes: null }));
                    }}
                    onBlur={handleBlur("search")}
                  />
                  {type}
                </label>
              ))}
            </div>
            {errors.propertyTypes && (
              <div className="error-message">{errors.propertyTypes}</div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">Количество комнат</label>
            <select
              className="form-select"
              value={searchForm.rooms}
              onChange={(e) =>
                setSearchForm((prev) => ({ ...prev, rooms: e.target.value }))
              }
            >
              <option value="">Выберите</option>
              {["Студия", "1", "2", "3", "4", "5+"].map((rooms) => (
                <option key={rooms} value={rooms}>
                  {rooms}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Район</label>
            <input
              type="text"
              className="form-input"
              placeholder="Например: Ворошиловский район"
              value={searchForm.district}
              onChange={(e) =>
                setSearchForm((prev) => ({ ...prev, district: e.target.value }))
              }
            />
          </div>
          <div className="form-group">
            <label className="form-label">Бюджет</label>
            <div className="form-row">
              <div className="form-group">
                <input
                  type="number"
                  className="form-input"
                  placeholder="От $"
                  value={searchForm.budgetMin}
                  onChange={(e) =>
                    setSearchForm((prev) => ({
                      ...prev,
                      budgetMin: e.target.value,
                    }))
                  }
                />
              </div>
              <div className="form-group">
                <input
                  type="number"
                  className="form-input"
                  name="budgetMax"
                  placeholder="До $"
                  value={searchForm.budgetMax}
                  onChange={(e) => {
                    setSearchForm((prev) => ({
                      ...prev,
                      budgetMax: e.target.value,
                    }));
                    setErrors((prev) => ({ ...prev, budgetMax: null }));
                  }}
                  onBlur={handleBlur("search")}
                />
                {errors.budgetMax && (
                  <div className="error-message">{errors.budgetMax}</div>
                )}
              </div>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Дополнительные пожелания</label>
            <textarea
              className="form-textarea"
              placeholder="Опишите дополнительные пожелания..."
              value={searchForm.requirements}
              onChange={(e) =>
                setSearchForm((prev) => ({
                  ...prev,
                  requirements: e.target.value,
                }))
              }
            />
          </div>
          <div className="form-group">
            <label className="form-label">
              Ваше имя <span className="required">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              name="name"
              value={searchForm.name}
              onChange={(e) => {
                setSearchForm((prev) => ({ ...prev, name: e.target.value }));
                setErrors((prev) => ({ ...prev, name: null }));
              }}
              onBlur={handleBlur("search")}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">
              Номер телефона <span className="required">*</span>
            </label>
            <input
              type="tel"
              className="form-input"
              name="phone"
              placeholder="+7 (XXX) XXX-XX-XX"
              value={searchForm.phone}
              onChange={(e) => {
                setSearchForm((prev) => ({ ...prev, phone: e.target.value }));
                setErrors((prev) => ({ ...prev, phone: null }));
              }}
              onBlur={handleBlur("search")}
            />
            {errors.phone && (
              <div className="error-message">{errors.phone}</div>
            )}
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting && <div className="loading-spinner"></div>}
            {isSubmitting ? "Отправка..." : "Отправить заявку"}
          </button>
        </form>
      </div>
    </div>
  );

  const OfferScreen = () => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen("main")}
        >
          ◀ Назад
        </button>
        <div className="header">
          <h1>Предложить объект</h1>
        </div>
        <form className="form" onSubmit={handleOfferSubmit}>
          <ProgressBar progress={offerProgress} />
          <div className="form-group">
            <label className="form-label">
              Тип сделки <span className="required">*</span>
            </label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Продать"
                  checked={offerForm.transactionType === "Продать"}
                  onChange={(e) => {
                    setOfferForm((prev) => ({
                      ...prev,
                      transactionType: e.target.value,
                    }));
                    setErrors((prev) => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur("offer")}
                />
                Продать
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Сдать"
                  checked={offerForm.transactionType === "Сдать"}
                  onChange={(e) => {
                    setOfferForm((prev) => ({
                      ...prev,
                      transactionType: e.target.value,
                    }));
                    setErrors((prev) => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur("offer")}
                />
                Сдать
              </label>
            </div>
            {errors.transactionType && (
              <div className="error-message">{errors.transactionType}</div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">
              Тип недвижимости <span className="required">*</span>
            </label>
            <select
              className="form-select"
              name="propertyType"
              value={offerForm.propertyType}
              onChange={(e) => {
                setOfferForm((prev) => ({
                  ...prev,
                  propertyType: e.target.value,
                }));
                setErrors((prev) => ({ ...prev, propertyType: null }));
              }}
              onBlur={handleBlur("offer")}
            >
              <option value="">Выберите тип</option>
              {["Квартира", "Дом", "Коммерческая недвижимость"].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            {errors.propertyType && (
              <div className="error-message">{errors.propertyType}</div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">
              Адрес <span className="required">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              name="address"
              placeholder="Улица, дом, квартира"
              value={offerForm.address}
              onChange={(e) => {
                setOfferForm((prev) => ({ ...prev, address: e.target.value }));
                setErrors((prev) => ({ ...prev, address: null }));
              }}
              onBlur={handleBlur("offer")}
            />
            {errors.address && (
              <div className="error-message">{errors.address}</div>
            )}
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Площадь</label>
              <input
                type="number"
                className="form-input"
                placeholder="м²"
                value={offerForm.area}
                onChange={(e) =>
                  setOfferForm((prev) => ({ ...prev, area: e.target.value }))
                }
              />
            </div>
            <div className="form-group">
              <label className="form-label">Этаж</label>
              <input
                type="text"
                className="form-input"
                placeholder="Например: 5/9"
                value={offerForm.floors}
                onChange={(e) =>
                  setOfferForm((prev) => ({ ...prev, floors: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Количество комнат</label>
              <input
                type="number"
                className="form-input"
                value={offerForm.rooms}
                onChange={(e) =>
                  setOfferForm((prev) => ({ ...prev, rooms: e.target.value }))
                }
              />
            </div>
            <div className="form-group">
              <label className="form-label">Цена</label>
              <input
                type="number"
                className="form-input"
                placeholder="$"
                value={offerForm.price}
                onChange={(e) =>
                  setOfferForm((prev) => ({ ...prev, price: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Описание</label>
            <textarea
              className="form-textarea"
              placeholder="Подробное описание объекта..."
              value={offerForm.description}
              onChange={(e) =>
                setOfferForm((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
            />
          </div>
          <div className="form-group">
            <label className="form-label">Фотографии</label>
            <div
              className="upload-zone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, "photos")}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="upload-text">
                Перетащите фото сюда или нажмите для выбора
              </div>
              <div className="upload-hint">Максимум 10 фотографий</div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".jpg,.jpeg,.png,.webp"
                onChange={(e) => handleFileUpload(e.target.files, "photos")}
              />
            </div>
            {offerForm.photos.length > 0 && (
              <div className="file-previews">
                {offerForm.photos.map((photo, index) => (
                  <div key={index} className="file-preview">
                    <img src={URL.createObjectURL(photo)} alt="Preview" />
                    <button
                      type="button"
                      className="file-preview-remove"
                      onClick={() => removePhoto(index)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">Видео</label>
            <div
              className="upload-zone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, "video")}
              onClick={() => videoInputRef.current?.click()}
            >
              <div className="upload-text">
                Перетащите видео сюда или нажмите для выбора
              </div>
              <div className="upload-hint">Максимум 1 видео (до 50 МБ)</div>
              <input
                ref={videoInputRef}
                type="file"
                accept=".mp4,.mov"
                onChange={(e) => handleFileUpload(e.target.files, "video")}
              />
            </div>
            {offerForm.video && (
              <div className="video-preview">
                <div className="video-info">
                  <div className="video-name">🎥 {offerForm.video.name}</div>
                  <div className="video-size">
                    {formatFileSize(offerForm.video.size)}
                  </div>
                </div>
                <button
                  type="button"
                  className="file-preview-remove"
                  onClick={removeVideo}
                >
                  ×
                </button>
              </div>
            )}
          </div>
          <div className="form-group">
            <label className="form-label">
              Ваше имя <span className="required">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              name="name"
              value={offerForm.name}
              onChange={(e) => {
                setOfferForm((prev) => ({ ...prev, name: e.target.value }));
                setErrors((prev) => ({ ...prev, name: null }));
              }}
              onBlur={handleBlur("offer")}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">
              Номер телефона <span className="required">*</span>
            </label>
            <input
              type="tel"
              className="form-input"
              name="phone"
              placeholder="+7 (XXX) XXX-XX-XX"
              value={offerForm.phone}
              onChange={(e) => {
                setOfferForm((prev) => ({ ...prev, phone: e.target.value }));
                setErrors((prev) => ({ ...prev, phone: null }));
              }}
              onBlur={handleBlur("offer")}
            />
            {errors.phone && (
              <div className="error-message">{errors.phone}</div>
            )}
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting && <div className="loading-spinner"></div>}
            {isSubmitting ? "Отправка..." : "Отправить заявку"}
          </button>
        </form>
      </div>
    </div>
  );

  useEffect(() => {
    if (currentScreen === "favorites") {
      fetchFavorites();
    }
  }, [currentScreen]);

  const renderScreen = () => {
    switch (currentScreen) {
      case "search":
        return <SearchScreen />;
      case "offer":
        return <OfferScreen />;
      case "results":
        return (
          <ResultsScreen
            results={searchResults}
            onToggleFavorite={handleToggleFavorite}
            searchCriteria={searchForm}
            isLoading={isLoading}
          />
        );
      case "favorites":
        return (
          <FavoritesScreen
            favorites={favorites}
            onToggleFavorite={handleToggleFavorite}
            isLoading={isLoading}
          />
        );
      case "map":
        return <MapScreen />;
      case "chat":
        return <ChatScreen />;
      default:
        return <MainScreen />;
    }
  };

  return (
    <>
      {renderScreen()}
      {modal && (
        <div className="modal">
          <div className="modal-content">
            <div
              className={`modal-text ${modal.type === "success" ? "success-text" : "error-text"}`}
            >
              {modal.message}
            </div>
            {modal.type === "error" && (
              <button
                className="btn btn-primary"
                onClick={() => setModal(null)}
              >
                OK
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
};

ReactDOM.render(<DonEstateApp />, document.getElementById("root"));
