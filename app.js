const { useState, useCallback, useRef, useEffect } = React;

/**
 * Main application component for the Don Estate Telegram Mini App.
 * Manages state, navigation between screens, form handling, and API interactions.
 * @returns {JSX.Element} The rendered application.
 */
const DonEstateApp = () => {
  const [currentScreen, setCurrentScreen] = useState('main');
  const [modal, setModal] = useState(null);

  // Search form state
  const [searchForm, setSearchForm] = useState({
    transactionType: '',
    propertyTypes: [],
    rooms: '',
    district: '',
    budgetMin: '',
    budgetMax: '',
    requirements: '',
    name: '',
    phone: ''
  });

  // Offer form state
  const [offerForm, setOfferForm] = useState({
    transactionType: '',
    propertyType: '',
    address: '',
    area: '',
    floors: '',
    rooms: '',
    price: '',
    description: '',
    name: '',
    phone: '',
    photos: [],
    video: null
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [mapProperties, setMapProperties] = useState([]);
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const [searchProgress, setSearchProgress] = useState(0);
  const [offerProgress, setOfferProgress] = useState(0);

  /**
   * A simple progress bar component.
   * @param {{progress: number}} props - The component props.
   * @returns {JSX.Element} The progress bar.
   */
  const ProgressBar = ({ progress }) => (
    <div className="progress-bar-container">
      <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      <div className="progress-text">{Math.round(progress)}%</div>
    </div>
  );

  /**
   * Effect to handle Telegram Web App theme changes.
   */
  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;

      const applyTheme = () => {
        if (tg.colorScheme === 'dark') {
          document.documentElement.setAttribute('data-color-scheme', 'dark');
        } else {
          document.documentElement.setAttribute('data-color-scheme', 'light');
        }
      };

      tg.onEvent('themeChanged', applyTheme);

      applyTheme(); // Apply theme on initial load

      // Cleanup
      return () => {
        tg.offEvent('themeChanged', applyTheme);
      };
    }
  }, []);

  /**
   * Effect to load form data from localStorage on initial render.
   */
  useEffect(() => {
    try {
      const savedSearchForm = localStorage.getItem('don_estate_search_form');
      if (savedSearchForm) {
        setSearchForm(JSON.parse(savedSearchForm));
      }

      const savedOfferForm = localStorage.getItem('don_estate_offer_form');
      if (savedOfferForm) {
        // We don't restore photos/video as they are file objects
        const parsedOfferForm = JSON.parse(savedOfferForm);
        delete parsedOfferForm.photos;
        delete parsedOfferForm.video;
        setOfferForm(prev => ({ ...prev, ...parsedOfferForm }));
      }
    } catch (error) {
      console.error("Failed to load form data from localStorage", error);
    }
  }, []);

  /**
   * Effect to save search form data to localStorage on change.
   */
  useEffect(() => {
    try {
      localStorage.setItem('don_estate_search_form', JSON.stringify(searchForm));
    } catch (error) {
      console.error("Failed to save search form data to localStorage", error);
    }
  }, [searchForm]);

  /**
   * Effect to save offer form data (excluding files) to localStorage on change.
   */
  useEffect(() => {
    try {
      const { photos, video, ...formDataToSave } = offerForm;
      localStorage.setItem('don_estate_offer_form', JSON.stringify(formDataToSave));
    } catch (error) {
      console.error("Failed to save offer form data to localStorage", error);
    }
  }, [offerForm]);

  /**
   * Effect to calculate the completion progress of the search form.
   */
  useEffect(() => {
    const requiredFields = ['transactionType', 'propertyTypes', 'name', 'phone'];
    const filledFields = requiredFields.filter(field => {
      const value = searchForm[field];
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return !!value;
    }).length;

    setSearchProgress((filledFields / requiredFields.length) * 100);
  }, [searchForm]);

  /**
   * Effect to calculate the completion progress of the offer form.
   */
  useEffect(() => {
    const requiredFields = ['transactionType', 'propertyType', 'address', 'name', 'phone'];
    const filledFields = requiredFields.filter(field => !!offerForm[field]).length;

    setOfferProgress((filledFields / requiredFields.length) * 100);
  }, [offerForm]);

  /**
   * Validates a phone number string.
   * @param {string} phone - The phone number to validate.
   * @returns {boolean} True if the phone number is valid.
   */
  const validatePhone = (phone) => {
    const pattern = /^[+]?[0-9]{10,15}$/;
    return pattern.test(phone.replace(/[\s\-\(\)]/g, ''));
  };

  /**
   * Validates a single form field.
   * @param {'search' | 'offer'} form - The name of the form.
   * @param {string} name - The name of the field to validate.
   * @param {*} value - The value of the field.
   * @returns {string|null} An error message, or null if valid.
   */
  const validateField = (form, name, value) => {
    const currentForm = form === 'search' ? searchForm : offerForm;

    switch (name) {
      case 'transactionType':
        return !value ? 'Выберите тип сделки' : null;
      case 'propertyTypes':
        return value.length === 0 ? 'Выберите хотя бы один тип недвижимости' : null;
      case 'name':
        return !value.trim() ? 'Введите ваше имя' : null;
      case 'phone':
        if (!value.trim()) return 'Введите номер телефона';
        if (!validatePhone(value)) return 'Введите корректный номер телефона';
        return null;
      case 'budgetMax':
        if (currentForm.budgetMin && value && parseFloat(value) <= parseFloat(currentForm.budgetMin)) {
          return 'Максимальная сумма должна быть больше минимальной';
        }
        return null;
      case 'propertyType':
        return !value ? 'Выберите тип недвижимости' : null;
      case 'address':
        return !value.trim() ? 'Введите адрес' : null;
      default:
        return null;
    }
  };

  /**
   * Creates a blur event handler for a form field to trigger validation.
   * @param {'search' | 'offer'} form - The form name.
   * @returns {function(React.FocusEvent): void} The onBlur event handler.
   */
  const handleBlur = (form) => (e) => {
    const { name, value } = e.target;
    const error = validateField(form, name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

  /**
   * Validates the entire search form.
   * @returns {Object} An object containing any validation errors.
   */
  const validateSearchForm = () => {
    const fieldsToValidate = ['transactionType', 'propertyTypes', 'name', 'phone', 'budgetMax'];
    const newErrors = {};
    fieldsToValidate.forEach(field => {
      const error = validateField('search', field, searchForm[field]);
      if (error) {
        newErrors[field] = error;
      }
    });
    return newErrors;
  };

  /**
   * Validates the entire offer form.
   * @returns {Object} An object containing any validation errors.
   */
  const validateOfferForm = () => {
    const fieldsToValidate = ['transactionType', 'propertyType', 'address', 'name', 'phone'];
    const newErrors = {};
    fieldsToValidate.forEach(field => {
      const error = validateField('offer', field, offerForm[field]);
      if (error) {
        newErrors[field] = error;
      }
    });
    return newErrors;
  };

  /**
   * Formats file size in bytes to a human-readable string.
   * @param {number} bytes - The file size in bytes.
   * @returns {string} The formatted file size.
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  /**
   * Handles file uploads for photos and videos, including validation.
   * @param {FileList} files - The list of files from the input.
   * @param {'photos' | 'video'} type - The type of upload.
   */
  const handleFileUpload = (files, type) => {
    const fileArray = Array.from(files);

    if (type === 'photos') {
      const validFiles = fileArray.filter(file => {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        const maxSize = 5 * 1024 * 1024; // 5MB
        return validTypes.includes(file.type) && file.size <= maxSize;
      });

      const currentPhotos = offerForm.photos.length;
      const totalPhotos = currentPhotos + validFiles.length;

      if (totalPhotos > 10) {
        setModal({
          type: 'error',
          message: 'Максимум 10 фотографий разрешено'
        });
        return;
      }

      setOfferForm(prev => ({
        ...prev,
        photos: [...prev.photos, ...validFiles]
      }));
    } else if (type === 'video') {
      const file = fileArray[0];
      const validTypes = ['video/mp4', 'video/mov'];
      const maxSize = 50 * 1024 * 1024; // 50MB

      if (!validTypes.includes(file.type)) {
        setModal({
          type: 'error',
          message: 'Поддерживаются только файлы MP4 и MOV'
        });
        return;
      }

      if (file.size > maxSize) {
        setModal({
          type: 'error',
          message: 'Размер видео не должен превышать 50 МБ'
        });
        return;
      }

      setOfferForm(prev => ({ ...prev, video: file }));
    }
  };

  /**
   * Removes a photo from the offer form state by its index.
   * @param {number} index - The index of the photo to remove.
   */
  const removePhoto = (index) => {
    setOfferForm(prev => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index)
    }));
  };

  /** Removes the video from the offer form state. */
  const removeVideo = () => {
    setOfferForm(prev => ({ ...prev, video: null }));
  };

  /** Drag-and-drop event handler for drag over. */
  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  /** Drag-and-drop event handler for drag leave. */
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
  };

  /**
   * Drag-and-drop event handler for drop.
   * @param {React.DragEvent} e - The drop event.
   * @param {'photos' | 'video'} type - The upload type.
   */
  const handleDrop = (e, type) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFileUpload(files, type);
  };

  /**
   * Handles the submission of the search form.
   * @param {React.FormEvent} e - The form submission event.
   */
  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateSearchForm();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
        body: JSON.stringify({
          transaction_type: searchForm.transactionType === 'Купить' ? 'sell' : 'rent',
          property_types: searchForm.propertyTypes.map(p => p.toLowerCase()),
          rooms: searchForm.rooms ? parseInt(searchForm.rooms) : undefined,
          district: searchForm.district,
          budget_min: searchForm.budgetMin ? parseFloat(searchForm.budgetMin) : undefined,
          budget_max: searchForm.budgetMax ? parseFloat(searchForm.budgetMax) : undefined,
          query_text: searchForm.requirements
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSearchResults(data.results);
      setCurrentScreen('results');

    } catch (error) {
      console.error("Failed to fetch search results:", error);
      setModal({
        type: 'error',
        message: 'Не удалось выполнить поиск. Пожалуйста, попробуйте еще раз.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handles the submission of the offer form.
   * @param {React.FormEvent} e - The form submission event.
   */
  const handleOfferSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateOfferForm();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    // Simulate API call
    setTimeout(() => {
      console.log('Offer Form Data:', {
        ...offerForm,
        photos: offerForm.photos.map(f => ({ name: f.name, size: f.size, type: f.type })),
        video: offerForm.video ? { name: offerForm.video.name, size: offerForm.video.size, type: offerForm.video.type } : null
      });
      setIsSubmitting(false);
      setModal({
        type: 'success',
        message: '✅ Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.'
      });

      // Reset form and navigate back
      setTimeout(() => {
        setOfferForm({
          transactionType: '',
          propertyType: '',
          address: '',
          area: '',
          floors: '',
          rooms: '',
          price: '',
          description: '',
          name: '',
          phone: '',
          photos: [],
          video: null
        });
        localStorage.removeItem('don_estate_offer_form');
        setModal(null);
        setCurrentScreen('main');
      }, 2000);
    }, 1500);
  };

  /**
   * Fetches the user's favorite properties from the API.
   */
  const fetchFavorites = async () => {
    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch('/api/favorites/', {
        headers: {
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
      });
      if (!response.ok) throw new Error('Failed to fetch favorites');
      const data = await response.json();
      setFavorites(data);
    } catch (error) {
      console.error(error);
      setModal({ type: 'error', message: 'Не удалось загрузить избранное.' });
    }
  };

  /**
   * Toggles a property's favorite status via an API call.
   * @param {string} propertyId - The ID of the property.
   * @param {boolean} isFavorite - The desired new favorite state.
   */
  const handleToggleFavorite = async (propertyId, isFavorite) => {
    try {
      const tg = window.Telegram.WebApp;
      const method = isFavorite ? 'POST' : 'DELETE';
      const url = isFavorite
        ? '/api/favorites/'
        : `/api/favorites/${propertyId}`;

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
        body: isFavorite ? JSON.stringify({ property_id: propertyId }) : null,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Optimistically update the UI
      const updateProperty = (p) => p.id === propertyId ? { ...p, is_favorite: isFavorite } : p;
      setSearchResults(prev => prev.map(updateProperty));

      if (isFavorite) {
        // Find the property in search results and add to favorites
        const propToAdd = searchResults.find(p => p.id === propertyId);
        if (propToAdd) {
            setFavorites(prev => [...prev, { ...propToAdd, is_favorite: true }]);
        }
      } else {
        // Remove from favorites
        setFavorites(prev => prev.filter(p => p.id !== propertyId));
      }

    } catch (error) {
      console.error("Failed to toggle favorite:", error);
      setModal({
        type: 'error',
        message: 'Не удалось обновить избранное.'
      });
    }
  };

  /**
   * Handles changes to the property type checkboxes in the search form.
   * @param {string} type - The property type.
   * @param {boolean} checked - The new checked state.
   */
  const handlePropertyTypeChange = (type, checked) => {
    setSearchForm(prev => ({
      ...prev,
      propertyTypes: checked
        ? [...prev.propertyTypes, type]
        : prev.propertyTypes.filter(t => t !== type)
    }));
  };

  /** The main landing screen with navigation buttons. */
  const MainScreen = () => (
    <div className="screen">
      <div className="container">
        <div className="header">
          <h1>Don Estate</h1>
          <p>Агентство недвижимости в Донецке</p>
        </div>

        <div className="main-buttons">
          <button
            className="btn btn-primary"
            onClick={() => setCurrentScreen('search')}
          >
            🔍 Найти недвижимость
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen('offer')}
          >
            🏠 Предложить объект
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen('favorites')}
          >
            ❤️ Избранное
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setCurrentScreen('map')}
          >
            🗺️ Карта
          </button>
        </div>
      </div>
    </div>
  );

  const PropertyCard = ({ property, onToggleFavorite }) => (
    <div className="property-card">
      <div className="property-card__image-container">
        {property.photos && property.photos.length > 0 ? (
          <img src={property.photos[0]} alt={property.title} className="property-card__image" />
        ) : (
          <div className="property-card__no-image">Нет фото</div>
        )}
        <button
          className={`property-card__favorite-btn ${property.is_favorite ? 'active' : ''}`}
          onClick={() => onToggleFavorite(property.id, !property.is_favorite)}
        >
          ❤️
        </button>
      </div>
      <div className="property-card__content">
        <h3 className="property-card__title">{property.title}</h3>
        <p className="property-card__price">{property.price_usd ? `$${property.price_usd.toLocaleString()}` : 'Цена не указана'}</p>
        <p className="property-card__address">{property.address || 'Адрес не указан'}</p>
        <p className="property-card__description">{property.description}</p>
      </div>
    </div>
  );

  const ResultsScreen = ({ results, onToggleFavorite }) => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen('search')}
        >
          ◀ Назад к поиску
        </button>
        <div className="header">
          <h1>Результаты поиска</h1>
        </div>
        <div className="results-list">
          {results.length > 0 ? (
            results.map(prop =>
              <PropertyCard
                key={prop.id}
                property={prop}
                onToggleFavorite={onToggleFavorite}
              />)
          ) : (
            <p>Ничего не найдено. Попробуйте изменить критерии поиска.</p>
          )}
        </div>
      </div>
    </div>
  );

  const FavoritesScreen = ({ favorites, onToggleFavorite }) => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen('main')}
        >
          ◀ Назад
        </button>
        <div className="header">
          <h1>Избранное</h1>
        </div>
        <div className="results-list">
          {favorites.length > 0 ? (
            favorites.map(prop =>
              <PropertyCard
                key={prop.id}
                property={prop}
                onToggleFavorite={onToggleFavorite}
              />)
          ) : (
            <p>Вы еще ничего не добавили в избранное.</p>
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
            // Add a placemark for the user's location
            const userPlacemark = new ymaps.Placemark(userCoords, {
              hintContent: 'Вы здесь'
            }, {
              preset: 'islands#geolocationIcon',
              iconColor: '#ff0000'
            });
            mapInstance.current.geoObjects.add(userPlacemark);
          }
        });
      }
    };

    useEffect(() => {
      const initMap = () => {
        if (!mapRef.current) return;

        mapInstance.current = new ymaps.Map(mapRef.current, {
          center: [48.015, 37.802], // Donetsk center
          zoom: 12
        });

        // Fetch properties and add placemarks
        fetchMapProperties(mapInstance.current);
      };

      ymaps.ready(initMap);
    }, []);

    const fetchMapProperties = async (map) => {
      try {
        const response = await fetch('/api/map/properties');
        if (!response.ok) throw new Error('Failed to fetch map properties');
        const properties = await response.json();
        setMapProperties(properties);

        properties.forEach(prop => {
          const placemark = new ymaps.Placemark([prop.latitude, prop.longitude], {
            balloonContentHeader: prop.title,
            balloonContentBody: `$${prop.price_usd.toLocaleString()}`,
            hintContent: prop.title
          });
          map.geoObjects.add(placemark);
        });

      } catch (error) {
        console.error(error);
        setModal({ type: 'error', message: 'Не удалось загрузить объекты на карте.' });
      }
    };

    return (
      <div className="screen map-screen">
        <div id="map" ref={mapRef} style={{ width: '100%', height: '100%' }}></div>
        <button
          className="btn btn-back map-back-btn"
          onClick={() => setCurrentScreen('main')}
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

  const SearchScreen = () => (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen('main')}
        >
          ◀ Назад
        </button>

        <div className="header">
          <h1>Найти недвижимость</h1>
        </div>

        <form className="form" onSubmit={handleSearchSubmit}>
          <ProgressBar progress={searchProgress} />
          <div className="form-group">
            <label className="form-label">Тип сделки <span className="required">*</span></label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Купить"
                  checked={searchForm.transactionType === 'Купить'}
                  onChange={(e) => {
                    setSearchForm(prev => ({ ...prev, transactionType: e.target.value }));
                    setErrors(prev => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur('search')}
                />
                Купить
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Снять"
                  checked={searchForm.transactionType === 'Снять'}
                  onChange={(e) => {
                    setSearchForm(prev => ({ ...prev, transactionType: e.target.value }));
                    setErrors(prev => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur('search')}
                />
                Снять
              </label>
            </div>
            {errors.transactionType && <div className="error-message">{errors.transactionType}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Тип недвижимости <span className="required">*</span></label>
            <div className="checkbox-group">
              {['Квартира', 'Дом', 'Коммерческая недвижимость'].map(type => (
                <label key={type} className="checkbox-option">
                  <input
                    type="checkbox"
                    name="propertyTypes"
                    checked={searchForm.propertyTypes.includes(type)}
                    onChange={(e) => {
                      handlePropertyTypeChange(type, e.target.checked);
                      setErrors(prev => ({ ...prev, propertyTypes: null }));
                    }}
                    onBlur={handleBlur('search')}
                  />
                  {type}
                </label>
              ))}
            </div>
            {errors.propertyTypes && <div className="error-message">{errors.propertyTypes}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Количество комнат</label>
            <select
              className="form-select"
              value={searchForm.rooms}
              onChange={(e) => setSearchForm(prev => ({ ...prev, rooms: e.target.value }))}
            >
              <option value="">Выберите</option>
              {['Студия', '1', '2', '3', '4', '5+'].map(rooms => (
                <option key={rooms} value={rooms}>{rooms}</option>
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
              onChange={(e) => setSearchForm(prev => ({ ...prev, district: e.target.value }))}
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
                  onChange={(e) => setSearchForm(prev => ({ ...prev, budgetMin: e.target.value }))}
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
                    setSearchForm(prev => ({ ...prev, budgetMax: e.target.value }));
                    setErrors(prev => ({ ...prev, budgetMax: null }));
                  }}
                  onBlur={handleBlur('search')}
                />
                {errors.budgetMax && <div className="error-message">{errors.budgetMax}</div>}
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Дополнительные пожелания</label>
            <textarea
              className="form-textarea"
              placeholder="Опишите дополнительные пожелания..."
              value={searchForm.requirements}
              onChange={(e) => setSearchForm(prev => ({ ...prev, requirements: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Ваше имя <span className="required">*</span></label>
            <input
              type="text"
              className="form-input"
              name="name"
              value={searchForm.name}
              onChange={(e) => {
                setSearchForm(prev => ({ ...prev, name: e.target.value }));
                setErrors(prev => ({ ...prev, name: null }));
              }}
              onBlur={handleBlur('search')}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Номер телефона <span className="required">*</span></label>
            <input
              type="tel"
              className="form-input"
              name="phone"
              placeholder="+7 (XXX) XXX-XX-XX"
              value={searchForm.phone}
              onChange={(e) => {
                setSearchForm(prev => ({ ...prev, phone: e.target.value }));
                setErrors(prev => ({ ...prev, phone: null }));
              }}
              onBlur={handleBlur('search')}
            />
            {errors.phone && <div className="error-message">{errors.phone}</div>}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting && <div className="loading-spinner"></div>}
            {isSubmitting ? 'Отправка...' : 'Отправить заявку'}
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
          onClick={() => setCurrentScreen('main')}
        >
          ◀ Назад
        </button>

        <div className="header">
          <h1>Предложить объект</h1>
        </div>

        <form className="form" onSubmit={handleOfferSubmit}>
          <ProgressBar progress={offerProgress} />
          <div className="form-group">
            <label className="form-label">Тип сделки <span className="required">*</span></label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Продать"
                  checked={offerForm.transactionType === 'Продать'}
                  onChange={(e) => {
                    setOfferForm(prev => ({ ...prev, transactionType: e.target.value }));
                    setErrors(prev => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur('offer')}
                />
                Продать
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name="transactionType"
                  value="Сдать"
                  checked={offerForm.transactionType === 'Сдать'}
                  onChange={(e) => {
                    setOfferForm(prev => ({ ...prev, transactionType: e.target.value }));
                    setErrors(prev => ({ ...prev, transactionType: null }));
                  }}
                  onBlur={handleBlur('offer')}
                />
                Сдать
              </label>
            </div>
            {errors.transactionType && <div className="error-message">{errors.transactionType}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Тип недвижимости <span className="required">*</span></label>
            <select
              className="form-select"
              name="propertyType"
              value={offerForm.propertyType}
              onChange={(e) => {
                setOfferForm(prev => ({ ...prev, propertyType: e.target.value }));
                setErrors(prev => ({ ...prev, propertyType: null }));
              }}
              onBlur={handleBlur('offer')}
            >
              <option value="">Выберите тип</option>
              {['Квартира', 'Дом', 'Коммерческая недвижимость'].map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            {errors.propertyType && <div className="error-message">{errors.propertyType}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Адрес <span className="required">*</span></label>
            <input
              type="text"
              className="form-input"
              name="address"
              placeholder="Улица, дом, квартира"
              value={offerForm.address}
              onChange={(e) => {
                setOfferForm(prev => ({ ...prev, address: e.target.value }));
                setErrors(prev => ({ ...prev, address: null }));
              }}
              onBlur={handleBlur('offer')}
            />
            {errors.address && <div className="error-message">{errors.address}</div>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Площадь</label>
              <input
                type="number"
                className="form-input"
                placeholder="м²"
                value={offerForm.area}
                onChange={(e) => setOfferForm(prev => ({ ...prev, area: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Этаж</label>
              <input
                type="text"
                className="form-input"
                placeholder="Например: 5/9"
                value={offerForm.floors}
                onChange={(e) => setOfferForm(prev => ({ ...prev, floors: e.target.value }))}
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
                onChange={(e) => setOfferForm(prev => ({ ...prev, rooms: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Цена</label>
              <input
                type="number"
                className="form-input"
                placeholder="$"
                value={offerForm.price}
                onChange={(e) => setOfferForm(prev => ({ ...prev, price: e.target.value }))}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Описание</label>
            <textarea
              className="form-textarea"
              placeholder="Подробное описание объекта..."
              value={offerForm.description}
              onChange={(e) => setOfferForm(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Фотографии</label>
            <div
              className="upload-zone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, 'photos')}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="upload-text">Перетащите фото сюда или нажмите для выбора</div>
              <div className="upload-hint">Максимум 10 фотографий</div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".jpg,.jpeg,.png,.webp"
                onChange={(e) => handleFileUpload(e.target.files, 'photos')}
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
              onDrop={(e) => handleDrop(e, 'video')}
              onClick={() => videoInputRef.current?.click()}
            >
              <div className="upload-text">Перетащите видео сюда или нажмите для выбора</div>
              <div className="upload-hint">Максимум 1 видео (до 50 МБ)</div>
              <input
                ref={videoInputRef}
                type="file"
                accept=".mp4,.mov"
                onChange={(e) => handleFileUpload(e.target.files, 'video')}
              />
            </div>
            {offerForm.video && (
              <div className="video-preview">
                <div className="video-info">
                  <div className="video-name">🎥 {offerForm.video.name}</div>
                  <div className="video-size">{formatFileSize(offerForm.video.size)}</div>
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
            <label className="form-label">Ваше имя <span className="required">*</span></label>
            <input
              type="text"
              className="form-input"
              name="name"
              value={offerForm.name}
              onChange={(e) => {
                setOfferForm(prev => ({ ...prev, name: e.target.value }));
                setErrors(prev => ({ ...prev, name: null }));
              }}
              onBlur={handleBlur('offer')}
            />
            {errors.name && <div className="error-message">{errors.name}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Номер телефона <span className="required">*</span></label>
            <input
              type="tel"
              className="form-input"
              name="phone"
              placeholder="+7 (XXX) XXX-XX-XX"
              value={offerForm.phone}
              onChange={(e) => {
                setOfferForm(prev => ({ ...prev, phone: e.target.value }));
                setErrors(prev => ({ ...prev, phone: null }));
              }}
              onBlur={handleBlur('offer')}
            />
            {errors.phone && <div className="error-message">{errors.phone}</div>}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting && <div className="loading-spinner"></div>}
            {isSubmitting ? 'Отправка...' : 'Отправить заявку'}
          </button>
        </form>
      </div>
    </div>
  );

  useEffect(() => {
    if (currentScreen === 'favorites') {
      fetchFavorites();
    }
  }, [currentScreen]);

  const renderScreen = () => {
    switch (currentScreen) {
      case 'search': return <SearchScreen />;
      case 'offer': return <OfferScreen />;
      case 'results': return <ResultsScreen results={searchResults} onToggleFavorite={handleToggleFavorite} />;
      case 'favorites': return <FavoritesScreen favorites={favorites} onToggleFavorite={handleToggleFavorite} />;
      case 'map': return <MapScreen />;
      default: return <MainScreen />;
    }
  };

  return (
    <>
      {renderScreen()}
      {modal && (
        <div className="modal">
          <div className="modal-content">
            <div className={`modal-text ${modal.type === 'success' ? 'success-text' : 'error-text'}`}>
              {modal.message}
            </div>
            {modal.type === 'error' && (
              <button className="btn btn-primary" onClick={() => setModal(null)}>
                OK
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
};

ReactDOM.render(<DonEstateApp />, document.getElementById('root'));
