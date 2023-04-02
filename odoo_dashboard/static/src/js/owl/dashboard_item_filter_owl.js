odoo.define('odoo_dashboard_builder.DashboardItemFilter', function (require) {
    "use strict";

    const { Component } = owl;
    const { useState, useRef } = owl.hooks;


    class Filter extends Component {

        state = useState({
            select: ''
        });

        selectedTag = useRef("selectionTag");
        dropdownTag = useRef('dropdownTag');

        constructor(parent, params, key) {
            super(parent, params, key);
            this.line_icon = params.line_icon;
            this.key = key;
            this.custom_event = this.key;
            this.icon = params.icon;
            this.options = params.options;
            this.select = params.select;
            this.state.select = this.select;
            this.initParameter(params);
        }

        initParameter(params) {
            this.displayMode = true;
            this.type = params.type;
            this.selectedId = this.key + '-' + this.env.displayID;
        }

        onValueChange() {
            let payload = { key: this.custom_event, value: this.select };
            this.trigger('change-filter-value', payload);
        }
        changeSelectedOption(option) {
            let target = $(this.dropdownTag.el).find(`[val=${option}]`);
            if (option !== this.select) {
                this._changeSelectedOption(option);
                this.__changeSelected(target);
            }
        }

        _changeSelectedOption(option) {
            this.select = option;
            let val = this.options[option];
            this.selectedTag.el.innerHTML = this.line_icon ? val[0] : val;
        }

        mounted() {
            super.mounted(...arguments);
        }

        __changeSelected(el) {
            el.siblings('.selected').removeClass('selected');
            el.addClass('selected');
        }


        _selectedChange(e) {
            e.stopPropagation();
            this.selectedTag.el.classList.remove("select-arrow-active");
            this.dropdownTag.el.classList.add("select-hide");
            $(this.selectedTag.el).parents('.many2one').toggleClass('active');
            let target = $(e.target).closest('div');
            let val = target.attr('val');
            if (val !== this.select) {
                this._changeSelectedOption(val);
                this.__changeSelected(target);
                this.onValueChange();
            }
        }

        _showingDropdown(e) {
            if (window.selectOpen && window.selectOpen !== this.selectedTag.el) {
                window.selectOpen.classList.remove("select-arrow-active");
                $(window.selectOpen).next('.select-items').addClass('select-hide');
                $(window.selectOpen).parents('.many2one').removeClass('active');
            }
            e.stopPropagation();
            window.selectOpen = this.selectedTag.el;
            this.dropdownTag.el.classList.toggle("select-hide");
            this.selectedTag.el.classList.toggle("select-arrow-active");
            $(this.selectedTag.el).parents('.many2one').toggleClass('active');
        }
    }

    Filter.template = 'BaseFilter';

    class Restrict extends Component {

        state = useState({
            select: '',
            max: '',
        });

        nextButton = useRef("NextButton");
        previousButton = useRef('PreviousButton');
        previousTag = useRef("PreviousTag");
        nextTag = useRef('NextTag');
        maxTag = useRef('MaxTag')

        constructor(parent, params, key) {
            super(parent, params, key);
            this.parent = parent;
            this.key = key;
            this.icon = params.icon;
            this.select = params.select;
            this.state.select = this.select
            this.initParameter(params);
        }

        initParameter(params) {
            this.displayMode = true;
            this.type = params.type;
            this.selectedId = this.key + '-' + this.env.displayID;
            this.value = this.select.split('-');
            this.offset = 1//parseInt(this.value[0]);
            this.end = 30//parseInt(this.value[1]);
            this.limit = this.end - this.offset + 1;
            this.max = this.end;
            this.hasChange = false;
        }

        mounted(){
            super.mounted(...arguments);
            this.trigger('trigger-reset-paging-event', ()=>this.resetPaging(this))
        }

        updateMaximum(data) {
            this.handleUIOnDemo(data.isDemo);
            data = data.value;
            if (this.end > data) {
                this.end = data;
                this.nextTag.el.innerText = this.end;
            }
            if (this.end < this.offset) {
                this.offset = this.end;
            }
            this.max = data;
            this.maxTag.el.innerHTML = this.max;
        }

        handleUIOnDemo(isDemo){
            this.el.style.display= ((isDemo)?'none':'unset');
        }

        resetPaging(dontLoad = true){
            this.offset = 1;
            this.end = this.value[1];
            this.limit = this.end - this.offset + 1;
            this.max = this.value[1];
            this.el.style.display = 'none';
            this.onValueChange(dontLoad);
        }

        changePagingLayout(){
            this.nextTag.el.innerText = this.end;
            this.previousTag.el.innerText = this.offset;
        }

        onValueChange(dontLoad) {
            this.changePagingLayout()
            let val = String(this.offset) + "-" + this.end;
            let payload = { key: this.key, value: val, dontSave: true};
            if (dontLoad){
                payload.dontLoad = dontLoad;
            }
            this.trigger('change-filter-value', payload);
        }

        __checkNumeric(n) {
            if (n <= 0) n = 1;
            return n;
        }

        _onListKeyDown(evt) {
            let keycode = evt.keyCode;
            this.hasChange = true;
            if (keycode === 13) {
                let offset = this.__checkNumeric(parseInt(this.previousTag.el.innerText));
                let end = parseInt(this.nextTag.el.innerText)
                if (end >= this.max) {
                    end = this.max;
                }
                else if (end < offset) {
                    end = offset
                }

                if (end >= offset) {
                    this.offset = offset;
                    this.end = end;
                    this.hasChange = false;
                    this.onValueChange();
                }
                this.limit = this.end - this.offset + 1;
                evt.preventDefault();
            } else if (
                !(keycode > 47 && keycode < 58)
                && !(keycode > 95 && keycode < 106)
                && keycode !== 8
                && keycode !== 46
                && keycode !== 39
                && keycode !== 37
            ) {
                evt.preventDefault();
            } else {
                this.hasChange = false
            }
        }

        _ChangeListRange(key) {
            if (this.hasChange) {
                this.offset = parseInt(this.previousTag.el.innerText);
                this.end = parseInt(this.nextTag.el.innerText);
                this.limit = this.end - this.offset + 1;
                this.hasChange = false;
            }
            let direction = 0
            if (key === 'next'){
                direction = 1;
            }
            else if (key === 'prev'){
                direction = -1;
            }
            let currentMinimum = (this.offset + this.limit * direction);
            if (currentMinimum > this.max) {
                currentMinimum = 1;
            } else if ((currentMinimum < 1) && (this.limit === 1)) {
                currentMinimum = this.max;
            } else if ((currentMinimum < 1) && (this.limit > 1)) {
                currentMinimum = this.max - ((this.max % this.limit) || this.limit) + 1;
            }
            this.offset = currentMinimum;
            this.end = this.offset + this.limit - 1;
            if (this.end > this.max){
                this.end = this.max;
            }
            this.onValueChange()
        }
    }

    Restrict.template = 'RestrictFilter';

    class Search extends Component {

        searchIp = useRef("search");
        constructor(parent, params, key) {
            super(parent, params, key);
            this.parent = parent
            this.key = key;
            this.initParameter(params);
        }


        initParameter(params) {
            this.displayMode = true;
            this.type = params.type;
            this.selectedId = this.key + '-' + this.env.displayID;
        }
        onUpdateSearchPlaceHolder(value) {
            this.searchName = value.value;
            this.searchIp.el.setAttribute('placeholder', `Search ${value.text} ...`)
        }
        _onKeyUp(evt) {
            if (evt.key === 'Enter' || evt.keyCode === 13) {
                this.onValueChange()
            }
        }

        onValueChange() {
            let value = {
                'name': this.searchName,
                'value': this.searchIp.el.value
            };
            let range = this.parent.filters['range'];
            if (range) {
                range.resetPaging();
            }
            let payload = {key: 'search', value: value, dontSave: true};
            this.trigger('change-filter-value', payload);
        }

    }

    Search.template = 'SearchFilter';

    return {
        'Filter': Filter,
        'Restrict': Restrict,
        'Search': Search
    };
});