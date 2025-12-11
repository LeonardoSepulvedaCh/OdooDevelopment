import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ContactRegistrationForm = publicWidget.Widget.extend({
  selector: "#wrap",
  events: {
    "change #state_id": "_onStateChange",
  },

  start() {
    this._super(...arguments);
    this._initializeCityFilter();
  },

  _initializeCityFilter() {
    const stateSelect = this.el.querySelector("#state_id");
    const citySelect = this.el.querySelector("#city_id");

    if (!stateSelect || !citySelect) {
      return;
    }

    // Inicializar estado
    this._filterCities();
  },

  _onStateChange(ev) {
    this._filterCities();
  },

  _filterCities() {
    const stateSelect = this.el.querySelector("#state_id");
    const citySelect = this.el.querySelector("#city_id");

    if (!stateSelect || !citySelect) {
      return;
    }

    const selectedStateId = stateSelect.value;
    const cityOptions = citySelect.querySelectorAll("option");
    let visibleCount = 0;

    cityOptions.forEach((option) => {
      if (option.value === "") {
        // Opción por defecto siempre visible
        option.style.display = "";
        if (selectedStateId) {
          option.textContent = "Seleccione una ciudad";
        } else {
          option.textContent = "Seleccione primero un departamento";
        }
      } else {
        const cityStateId = option.dataset.stateId;

        if (cityStateId === selectedStateId) {
          option.style.display = "";
          option.disabled = false;
          visibleCount++;
        } else {
          option.style.display = "none";
          option.disabled = true;
        }
      }
    });

    // Resetear selección y habilitar/deshabilitar
    citySelect.value = "";
    citySelect.disabled = !selectedStateId || visibleCount === 0;
  },
});

export default publicWidget.registry.ContactRegistrationForm;
