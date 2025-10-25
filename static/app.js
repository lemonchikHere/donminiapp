const { useState, useCallback, useRef, useEffect } = React;

// Simple session cache
const apiCache = {};
let mapScriptLoaded = false;

const DonEstateApp = () => {
  const [currentScreen, setCurrentScreen] = useState('main');
  const [modal, setModal] = useState(null);
  const [toasts, setToasts] = useState([]);

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
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchOffset, setSearchOffset] = useState(0);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [mapProperties, setMapProperties] = useState([]);
  const [togglingFavorite, setTogglingFavorite] = useState(null); // Property ID
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const [searchProgress, setSearchProgress] = useState(0);
  const [offerProgress, setOfferProgress] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(null);

  // Simple in-memory cache
  const cache = useRef({});

  const getCache = (key) => {
    const entry = cache.current[key];
    if (entry && Date.now() < entry.expiry) {
      return entry.data;
    }
    return null;
  };

  const setCache = (key, data, ttl = 300000) => { // 5 minutes default TTL
    cache.current[key] = {
      data: data,
      expiry: Date.now() + ttl,
    };
  };

  const ProgressBar = ({ progress }) => (
    <div className="progress-bar-container">
      <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      <div className="progress-text">{Math.round(progress)}%</div>
    </div>
  );

  const showToast = (message) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 3000);
  };

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

  // Load form data from sessionStorage on initial render
  useEffect(() => {
    try {
      const savedSearchForm = sessionStorage.getItem('don_estate_search_form');
      if (savedSearchForm) {
        setSearchForm(JSON.parse(savedSearchForm));
      }

      const savedOfferForm = sessionStorage.getItem('don_estate_offer_form');
      if (savedOfferForm) {
        // We don't restore photos/video as they are file objects
        const parsedOfferForm = JSON.parse(savedOfferForm);
        delete parsedOfferForm.photos;
        delete parsedOfferForm.video;
        setOfferForm(prev => ({ ...prev, ...parsedOfferForm }));
      }
    } catch (error) {
      console.error("Failed to load form data from sessionStorage", error);
    }
  }, []);

  // Save search form data to sessionStorage
  useEffect(() => {
    try {
      sessionStorage.setItem('don_estate_search_form', JSON.stringify(searchForm));
    } catch (error) {
      console.error("Failed to save search form data to sessionStorage", error);
    }
  }, [searchForm]);

  // Save offer form data to sessionStorage (excluding files)
  useEffect(() => {
    try {
      const { photos, video, ...formDataToSave } = offerForm;
      sessionStorage.setItem('don_estate_offer_form', JSON.stringify(formDataToSave));
    } catch (error) {
      console.error("Failed to save offer form data to sessionStorage", error);
    }
  }, [offerForm]);

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

  useEffect(() => {
    const requiredFields = ['transactionType', 'propertyType', 'address', 'name', 'phone'];
    const filledFields = requiredFields.filter(field => !!offerForm[field]).length;

    setOfferProgress((filledFields / requiredFields.length) * 100);
  }, [offerForm]);

  const validatePhone = (phone) => {
    const pattern = /^[+]?[0-9]{10,15}$/;
    return pattern.test(phone.replace(/[\s\-\(\)]/g, ''));
  };

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

  const handleBlur = (form) => (e) => {
    const { name, value } = e.target;
    const error = validateField(form, name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

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
        showToast('Максимум 10 фотографий разрешено');
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
        showToast('Поддерживаются только файлы MP4 и MOV');
        return;
      }

      if (file.size > maxSize) {
        showToast('Размер видео не должен превышать 50 МБ');
        return;
      }

      setOfferForm(prev => ({ ...prev, video: file }));
    }
  };

  const removePhoto = (index) => {
    setOfferForm(prev => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index)
    }));
  };

  const removeVideo = () => {
    setOfferForm(prev => ({ ...prev, video: null }));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFileUpload(files, type);
  };

  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateSearchForm();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      const firstErrorField = Object.keys(validationErrors)[0];
      const errorElement = document.querySelector(`[name="${firstErrorField}"]`);
      if (errorElement) {
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setErrors({});
    setIsSubmitting(true);
    setIsLoading(true);
    setSearchResults([]); // Reset results for new search
    setSearchOffset(0);
    setSearchTotal(0);

    const searchRequestBody = {
      transaction_type: searchForm.transactionType === 'Купить' ? 'sell' : 'rent',
      property_types: searchForm.propertyTypes.map(p => p.toLowerCase()),
      rooms: searchForm.rooms ? parseInt(searchForm.rooms) : undefined,
      district: searchForm.district,
      budget_min: searchForm.budgetMin ? parseFloat(searchForm.budgetMin) : undefined,
      budget_max: searchForm.budgetMax ? parseFloat(searchForm.budgetMax) : undefined,
      query_text: searchForm.requirements
    };

    // For a new search, we don't use cache to ensure fresh results,
    // subsequent pagination for the *same* search will be cached by fetchMoreResults.
    // Let's clear the cache for this specific search key if it exists.
    const initialCacheKey = `search_${JSON.stringify(searchRequestBody)}_0`;
    if(apiCache[initialCacheKey]) {
        delete apiCache[initialCacheKey];
    }

    const cacheKey = `search_${JSON.stringify(searchForm)}`;
    const cachedResults = getCache(cacheKey);

    if (cachedResults) {
      setSearchResults(cachedResults);
      setCurrentScreen('results');
      setIsSubmitting(false);
      setIsLoading(false);
      return;
    }

    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch('/api/search?offset=0&limit=20', { // Fetch first page
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
        body: JSON.stringify(searchRequestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCache(cacheKey, data.results); // Save to cache
      setSearchResults(data.results);
      setSearchTotal(data.total);
      setSearchOffset(data.results.length);
      setCurrentScreen('results');

    } catch (error) {
      console.error("Failed to fetch search results:", error);
      showToast('Не удалось выполнить поиск. Пожалуйста, попробуйте еще раз.');
    } finally {
      setIsSubmitting(false);
      setIsLoading(false);
    }
  };

  const handleOfferSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validateOfferForm();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      const firstErrorField = Object.keys(validationErrors)[0];
      const errorElement = document.querySelector(`[name="${firstErrorField}"]`);
      if (errorElement) {
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setErrors({});
    setIsSubmitting(true);
    setUploadProgress(0);

    const formData = new FormData();
    Object.keys(offerForm).forEach(key => {
        if (key === 'photos') {
            offerForm.photos.forEach(photo => formData.append('photos', photo, photo.name));
        } else if (key === 'video') {
            if (offerForm.video) {
                formData.append('video', offerForm.video, offerForm.video.name);
            }
        } else {
            formData.append(key, offerForm[key]);
        }
    });

    const xhr = new XMLHttpRequest();

    xhr.open('POST', '/api/offers/', true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        setUploadProgress(percentComplete);
      }
    };

    xhr.onload = () => {
      setIsSubmitting(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setModal({
          type: 'success',
          message: '✅ Заявка успешно отправлена на модерацию!'
        });
        setTimeout(() => {
          setOfferForm({
            transactionType: '', propertyType: '', address: '', area: '',
            floors: '', rooms: '', price: '', description: '',
            name: '', phone: '', photos: [], video: null
          });
          sessionStorage.removeItem('don_estate_offer_form');
          setModal(null);
          setUploadProgress(null);
          setCurrentScreen('main');
        }, 2000);
      } else {
        showToast('Не удалось отправить заявку. Попробуйте снова.');
        setUploadProgress(null);
      }
    };

    xhr.onerror = () => {
      setIsSubmitting(false);
      showToast('Произошла сетевая ошибка. Проверьте подключение.');
      setUploadProgress(null);
    };

    xhr.send(formData);
  };

  const fetchFavorites = async () => {
    const cacheKey = 'favorites';
    if (apiCache[cacheKey]) {
      setFavorites(apiCache[cacheKey]);
      return;
    }

    setIsLoading(true);
    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch('/api/favorites/', {
        headers: {
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      apiCache[cacheKey] = data; // Cache the response
      setFavorites(data);
    } catch (error) {
      console.error("Failed to fetch favorites:", error);
      setModal({
        type: 'error',
        message: 'Не удалось загрузить избранное. Пожалуйста, проверьте ваше интернет-соединение и попробуйте снова.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFavorite = async (propertyId, isFavorite) => {
    // Optimistically update the UI first
    const originalFavorites = [...favorites];
    const originalSearchResults = [...searchResults];

    const updatePropertyUI = (p) => p.id === propertyId ? { ...p, is_favorite: isFavorite } : p;
    setSearchResults(prev => prev.map(updatePropertyUI));
    if (isFavorite) {
        const propToAdd = searchResults.find(p => p.id === propertyId);
        if (propToAdd) setFavorites(prev => [...prev, { ...propToAdd, is_favorite: true }]);
    } else {
        setFavorites(prev => prev.filter(p => p.id !== propertyId));
    }

    setTogglingFavorite(propertyId);

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

      // Invalidate cache on successful toggle
      Object.keys(apiCache).forEach(key => delete apiCache[key]);

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
      // Revert UI on error
      setFavorites(originalFavorites);
      setSearchResults(originalSearchResults);
      setModal({
        type: 'error',
        message: 'Не удалось обновить избранное. Пожалуйста, попробуйте еще раз.'
      });
    } finally {
      setTogglingFavorite(null);
    }
  };

  const handlePropertyTypeChange = (type, checked) => {
    setSearchForm(prev => ({
      ...prev,
      propertyTypes: checked
        ? [...prev.propertyTypes, type]
        : prev.propertyTypes.filter(t => t !== type)
    }));
  };

  const MainScreen = () => (
    <div className="screen">
      <div className="container">
        <div className="header">
          <img src="/static/assets/logo.jpg" alt="Don Estate" className="logo" />
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
          {/* <button
            className="btn btn-primary"
            onClick={() => setCurrentScreen('chat')}
          >
            💬 Чат с ассистентом
          </button> */}
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

  const PropertyCard = ({ property, onToggleFavorite, isToggling }) => (
    <div className="property-card">
      <div className="property-card__image-container">
        {property.photos && property.photos.length > 0 ? (
          <img src={property.photos[0]} alt={property.title} className="property-card__image" />
        ) : (
          <div className="property-card__no-image">Нет фото</div>
        )}
        <button
          className={`property-card__favorite-btn ${property.is_favorite ? 'active' : ''} ${isToggling ? 'loading' : ''}`}
          onClick={() => onToggleFavorite(property.id, !property.is_favorite)}
          disabled={isToggling}
        >
          {isToggling ? <div className="loading-spinner small"></div> : '❤️'}
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

  const fetchMoreResults = async () => {
    if (isFetchingMore || searchOffset >= searchTotal) return;

    setIsFetchingMore(true);

    const searchRequestBody = {
      transaction_type: searchForm.transactionType === 'Купить' ? 'sell' : 'rent',
      property_types: searchForm.propertyTypes.map(p => p.toLowerCase()),
      rooms: searchForm.rooms ? parseInt(searchForm.rooms) : undefined,
      district: searchForm.district,
      budget_min: searchForm.budgetMin ? parseFloat(searchForm.budgetMin) : undefined,
      budget_max: searchForm.budgetMax ? parseFloat(searchForm.budgetMax) : undefined,
      query_text: searchForm.requirements
    };

    const cacheKey = `search_${JSON.stringify(searchRequestBody)}_${searchOffset}`;

    if(apiCache[cacheKey]) {
        const data = apiCache[cacheKey];
        setSearchResults(prev => [...prev, ...data.results]);
        setSearchOffset(prev => prev + data.results.length);
        setIsFetchingMore(false);
        return;
    }

    try {
      const tg = window.Telegram.WebApp;
      const response = await fetch(`/api/search?offset=${searchOffset}&limit=20`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
        },
        body: JSON.stringify(searchRequestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      apiCache[cacheKey] = data; // Cache the new page
      setSearchResults(prev => [...prev, ...data.results]);
      setSearchOffset(prev => prev + data.results.length);

    } catch (error) {
      console.error("Failed to fetch more results:", error);
      // Optionally show a small error toast/message
    } finally {
      setIsFetchingMore(false);
    }
  };

  const ResultsScreen = ({ results, total, onToggleFavorite, searchCriteria, isLoading, isFetchingMore, onFetchMore }) => {

    useEffect(() => {
        const handleScroll = () => {
            // Check if we're near the bottom of the page
            if (window.innerHeight + document.documentElement.scrollTop < document.documentElement.offsetHeight - 200) return;
            onFetchMore();
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [onFetchMore]);

    const handleSaveSearch = async () => {
      try {
        const tg = window.Telegram.WebApp;
        const response = await fetch('/api/searches/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-telegram-user-id': tg.initDataUnsafe?.user?.id || '0',
          },
          body: JSON.stringify({ criteria: searchCriteria }),
        });
        if (!response.ok) throw new Error('Failed to save search');
        setModal({ type: 'success', message: '✅ Поиск сохранен! Мы будем уведомлять вас о новых объектах.' });
        setTimeout(() => setModal(null), 2000);
      } catch (error) {
        console.error("Failed to save search:", error);
        setModal({ type: 'error', message: 'Не удалось сохранить поиск. Пожалуйста, попробуйте еще раз.' });
      }
    };

    return (
    <div className="screen">
      <div className="container">
        <button
          className="btn btn-back"
          onClick={() => setCurrentScreen('search')}
        >
          ◀ Назад к поиску
        </button>
        <div className="header">
          <h1>Результаты поиска ({total})</h1>
          <button className="btn btn-secondary" onClick={handleSaveSearch}>
            💾 Сохранить поиск
          </button>
        </div>
        <div className="results-list">
          {isLoading ? (
            [...Array(3)].map((_, i) => <SkeletonCard key={i} />)
          ) : results.length > 0 ? (
            results.map(prop =>
              <PropertyCard
                key={prop.id}
                property={prop}
                onToggleFavorite={onToggleFavorite}
                isToggling={togglingFavorite === prop.id}
              />)
          ) : (
            <EmptyState
              icon="🤷"
              title="Ничего не найдено"
              message="Попробуйте изменить критерии поиска или расширить бюджет."
            />
          )}
          {isFetchingMore && <SkeletonCard />}
        </div>
      </div>
    </div>
  );

  const FavoritesScreen = ({ favorites, onToggleFavorite, isLoading }) => (
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
          {isLoading ? (
            [...Array(3)].map((_, i) => <SkeletonCard key={i} />)
          ) : favorites.length > 0 ? (
            favorites.map(prop =>
              <PropertyCard
                key={prop.id}
                property={prop}
                onToggleFavorite={onToggleFavorite}
                isToggling={togglingFavorite === prop.id}
              />)
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
    const [isMapLoading, setIsMapLoading] = useState(true);

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

    const loadMapScript = () => {
      return new Promise(async (resolve, reject) => {
        if (mapScriptLoaded) {
          return resolve();
        }
        try {
          const response = await fetch('/api/config/');
          const config = await response.json();
          const script = document.createElement('script');
          script.src = `https://api-maps.yandex.ru/2.1/?apikey=${config.yandex_maps_api_key}&lang=ru_RU`;
          script.async = true;
          script.onload = () => {
            mapScriptLoaded = true;
            ymaps.ready(resolve);
          };
          script.onerror = reject;
          document.head.appendChild(script);
        } catch (error) {
          console.error("Failed to load map config:", error);
          reject(error);
        }
      });
    };

    useEffect(() => {
      const initMap = () => {
        if (!mapRef.current || mapInstance.current) return;

        const savedMapState = JSON.parse(sessionStorage.getItem('don_estate_map_state'));

        mapInstance.current = new ymaps.Map(mapRef.current, {
          center: savedMapState?.center || [48.015, 37.802], // Donetsk center
          zoom: savedMapState?.zoom || 12
        });

        mapInstance.current.events.add(['boundschange'], () => {
            const mapState = {
                center: mapInstance.current.getCenter(),
                zoom: mapInstance.current.getZoom()
            };
            sessionStorage.setItem('don_estate_map_state', JSON.stringify(mapState));
        });

        // Fetch properties and add placemarks
        fetchMapProperties(mapInstance.current);
      };

      loadMapScript().then(initMap).catch(err => console.error("Map init failed", err));

      return () => {
        // We don't destroy the map instance to preserve it across screen changes
      };
    }, []);

    const fetchMapProperties = async (map) => {
      setIsLoading(true);
      const cacheKey = 'map_properties';
      let properties = getCache(cacheKey);

      if (properties) {
        setMapProperties(properties);
        addPlacemarksToMap(properties, map);
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch('/api/map/properties');
        if (!response.ok) throw new Error('Failed to fetch map properties');
        properties = await response.json();
        setCache(cacheKey, properties);
        setMapProperties(properties);
        addPlacemarksToMap(properties, map);
      } catch (error) {
        console.error("Failed to fetch map properties:", error);
        setModal({ type: 'error', message: 'Не удалось загрузить объекты на карте. Попробуйте позже.' });
      } finally {
        setIsLoading(false);
      }
    };

    const addPlacemarksToMap = (properties, map) => {
      properties.forEach(prop => {
        const placemark = new ymaps.Placemark([prop.latitude, prop.longitude], {
          balloonContentHeader: prop.title,
          balloonContentBody: `$${prop.price_usd.toLocaleString()}`,
          hintContent: prop.title
        });
        map.geoObjects.add(placemark);
      });
    };

    return (
      <div className="screen map-screen">
        {isMapLoading && (
          <div className="spinner-overlay">
            <div className="spinner"></div>
          </div>
        )}
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

  const ChatScreen = () => {
    const [messages, setMessages] = useState([
      { sender: 'bot', text: 'Здравствуйте! Чем могу помочь?' }
    ]);
    const [inputValue, setInputValue] = useState(sessionStorage.getItem('don_estate_chat_input') || '');
    const [isBotTyping, setIsBotTyping] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        sessionStorage.setItem('don_estate_chat_input', inputValue);
    }, [inputValue]);

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSendMessage = async (e) => {
      e.preventDefault();
      if (!inputValue.trim()) return;

      // Temporarily disabled chat
      setModal({ type: 'error', message: 'Чат временно недоступен.' });
      return;

      const userMessage = { sender: 'user', text: inputValue };
      setMessages(prev => [...prev, userMessage]);
      setInputValue('');
      setIsBotTyping(true);

      try {
        const response = await fetch('/api/chat/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: inputValue }),
        });

        if (!response.ok) throw new Error('Failed to get response from bot');

        const botResponse = await response.json();

        let botMessage = { sender: 'bot', text: 'Извините, я не смог обработать ваш запрос.' };
        if (botResponse.type === 'text') {
          botMessage.text = botResponse.content;
        } else if (botResponse.type === 'property_list') {
          botMessage.text = botResponse.summary;
          botMessage.properties = botResponse.properties;
        }

        setMessages(prev => [...prev, botMessage]);

      } catch (error) {
        console.error("Chat error:", error);
        setMessages(prev => [...prev, { sender: 'bot', text: 'Произошла ошибка сети. Не удалось связаться с ассистентом.' }]);
      } finally {
        setIsBotTyping(false);
      }
    };

    return (
      <div className="screen chat-screen">
        <div className="chat-header">
          <button className="btn btn-back" onClick={() => setCurrentScreen('main')}>◀</button>
          <h1>AI Ассистент</h1>
        </div>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              <p>{msg.text}</p>
              {msg.properties && (
                <div className="chat-property-cards">
                  {msg.properties.map(prop => (
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
          {isBotTyping && (
            <div className="chat-bubble bot typing">
              <div className="spinner"></div>
            </div>
          )}
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
          <button type="submit" disabled={isBotTyping}>➤</button>
        </form>
      </div>
    );
  };

  const SearchScreen = ({ setCurrentScreen, handleSearchSubmit, searchProgress, searchForm, setSearchForm, setErrors, handleBlur, errors, handlePropertyTypeChange, isSubmitting }) => (
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
          {uploadProgress !== null && (
            <div className="upload-progress-container">
              <div
                className="upload-progress-bar"
                style={{
                  width: `${uploadProgress}%`,
                  backgroundColor: `hsl(${uploadProgress * 1.2}, 100%, 45%)` // Red to Green
                }}
              ></div>
            </div>
          )}
        </form>
      </div>
    </div>
  );

  const OfferScreen = ({ setCurrentScreen, handleOfferSubmit, offerProgress, offerForm, setOfferForm, setErrors, handleBlur, errors, isSubmitting, handleFileUpload, removePhoto, removeVideo, fileInputRef, videoInputRef, formatFileSize }) => (
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
      case 'search':
        return <SearchScreen
          searchForm={searchForm}
          setSearchForm={setSearchForm}
          handleSearchSubmit={handleSearchSubmit}
          errors={errors}
          setErrors={setErrors}
          isSubmitting={isSubmitting}
          handleBlur={handleBlur}
          handlePropertyTypeChange={handlePropertyTypeChange}
          searchProgress={searchProgress}
          setCurrentScreen={setCurrentScreen}
        />;
      case 'offer':
        return <OfferScreen
            offerForm={offerForm}
            setOfferForm={setOfferForm}
            handleOfferSubmit={handleOfferSubmit}
            errors={errors}
            setErrors={setErrors}
            isSubmitting={isSubmitting}
            handleBlur={handleBlur}
            offerProgress={offerProgress}
            setCurrentScreen={setCurrentScreen}
            handleFileUpload={handleFileUpload}
            removePhoto={removePhoto}
            removeVideo={removeVideo}
            fileInputRef={fileInputRef}
            videoInputRef={videoInputRef}
            formatFileSize={formatFileSize}
        />;
      case 'results': return <ResultsScreen results={searchResults} onToggleFavorite={handleToggleFavorite} searchCriteria={searchForm} isLoading={isLoading} />;
      case 'favorites': return <FavoritesScreen favorites={favorites} onToggleFavorite={handleToggleFavorite} isLoading={isLoading} />;
      case 'map': return <MapScreen />;
      case 'chat': return <ChatScreen />;
      default: return <MainScreen />;
    }
  };

  return (
    <>
      {renderScreen()}
      {modal && modal.type === 'success' && (
        <div className="modal">
          <div className="modal-content">
            <div className="modal-text success-text">
              {modal.message}
            </div>
          </div>
        </div>
      )}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className="toast">
            {toast.message}
          </div>
        ))}
      </div>
    </>
  );
};

ReactDOM.render(
    <DonEstateApp />,
    document.getElementById('root')
);
