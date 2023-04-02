odoo.define('odoo_dashboard.DashboardItemSubcomponents', function (require) {
    "use strict";

    const {Component} = owl;
    const {useState, useRef} = owl.hooks;

    var Filter = require('odoo_dashboard.DashboardItemFilter');

    const parsingFilter = {
        'range':Filter.Restrict,
        'search': Filter.Search
    };

    class ItemNavigation extends Component {
        static template = 'ItemNavigation';
        popupContent = useRef("popup_content");
        baseContent = useRef('base_content')

        onClickAdvanceBtn(evt) {
            if (window.advanceItemPopup == this.popupContent.el) {
                window.advanceItemBase.classList.remove('trigger-advance')
                this.popupContent.el.style.display = 'none';
            } else {
                if (window.advanceItemPopup !== undefined) {
                    window.advanceItemPopup.style.display = 'none';
                    window.advanceItemBase.classList.remove('trigger-advance');
                }
                window.advanceItemPopup = this.popupContent.el;
                window.advanceItemBase = this.baseContent.el;
                this.popupContent.el.style.display = 'block';
                this.baseContent.el.classList.add('trigger-advance');
                evt.stopPropagation()
            }
        }

        onClickCopyBtn(evt) {
            this.trigger('item-advance-click', 'add');
            this.onClickAdvanceBtn(evt);
        }

        onClickMoveBtn(evt) {
            this.trigger('item-advance-click', 'move');
            this.onClickAdvanceBtn(evt);
        }

        onClickRemoveBtn(evt) {
            this.trigger('item-advance-click', 'drop');
        }

        onClickDuplicateBtn(evt) {
            this.trigger('item-advance-click', 'duplicate');
            this.onClickAdvanceBtn(evt);
        }
    }

    class ItemTitle extends Component {
        static template = 'ItemTitle';
        containerContent = useRef("container_content");
        popupContent = useRef("popup_content");
        textContent = useRef("text_content");
        iconContent = useRef("icon_content");

        constructor(parent, props) {
            super(parent, props);
            this.parent = parent;
            this.state = useState({
                title:'',
                description:'',
                titleSegment: [],
            });
            this.initTitleSegment();
        }

        initTitleSegment(){
            this.updateTitle(this.env.title.title, this.env.title.description);
        }
        updateTitle(title, description){
            if (typeof(title) === 'string' && title !== this.state.title){
                let titleSegment = title.split(' ');
                this.state.titleSegment = titleSegment.splice(0, titleSegment.length -1);
                this.state.finalTitleSegment = titleSegment[titleSegment.length -1];
            }
            if (typeof(description) === 'string' && description !== this.state.description){
                this.state.description = description;
            }
        }

        mounted() {
            super.mounted();
            this.trigger('title-state', {
                state: this.state,
                updateTitleF: (title, description)=>{this.updateTitle(title, description)}
            });
        }

        onRefreshItem() {
            this.trigger('refresh-btn-click');
        }

        onMouseOverPopup(evt) {
            $(this.popupContent.el).css('top', evt.clientY);
            $(this.popupContent.el).css('left', evt.clientX);
            this.popupContent.el.style.display = 'inline-block';
        }
        onMouseLeavePopup(evt){
            this.popupContent.el.style.display = 'none';
        }

        onClickItemTitle(evt) {
            this.trigger('item-title-click');
        }
    }

    class ItemControlBar extends Component {
        static template = 'ItemControlBar';
        filterContent = useRef("filter-content");

        constructor(parent, props) {
            super(parent, props);
            this.filters = {};
            this.props = props;
        }

        mounted() {
            super.mounted();
            var self = this;
            let obj = this.env.filterConfig;
            if (obj !== undefined) {
                Object.keys(obj).forEach(el => {
                        var newContent = `<div class="item periodic">
                                    <div class="${el}-content filter">
                                    </div>
                                    </div>`;
                        $(self.filterContent.el).append(newContent);
                        var filter_container = self.filterContent.el.getElementsByClassName(`${el}-content`)[0];
                        var filterOWL = parsingFilter[el] || Filter.Filter
                        var newFilter = new filterOWL(self, obj[el], el);
                        newFilter.mount(filter_container);
                        self.filters[el] = newFilter;
                    }
                );
                this.trigger('filter-rendered');
            }
        }

        willPatch() {
            super.willPatch();
            if (this.props['team'] && this.filters['team']) {
                this.filters['team'].changeSelectedOption(this.props.team.value);
            }
            if (this.props['range'] && this.filters['range']){
                this.filters['range'].updateMaximum(this.props.range);
            }
            if (this.props['search'] && this.filters['search']){
                this.filters['search'].onUpdateSearchPlaceHolder(this.props.search);
            }
        }
    }


    class ItemTitleFrame extends Component {
        static template = 'ItemTitleFrame';
        static components = {ItemNavigation, ItemTitle, ItemControlBar};
        constructor(parent, props) {
            super(parent, props);
            this.props = props;
        }
    }

    return {
        'ItemNavigation': ItemNavigation,
        'ItemTitle': ItemTitle,
        'ItemControlBar': ItemControlBar,
        'ItemTitleFrame': ItemTitleFrame,
    };
});