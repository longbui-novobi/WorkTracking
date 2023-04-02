odoo.define('odoo_dashboard.CustomFilterHook', function (require) {
    "use strict";

    function customDateRangeUIHook(rootElement) {
        const input = $(`<input d class="select-selected selected-input" type="period"/>`)
        const element = $(`
            <button class="dashboard_background_field_select btn_inline custom-date">
                <span class=" fa fa-calendar btn_icon_inline"></span>
            </button>`)
        element.append(input)
        element.insertAfter(rootElement)

        function setEvent(evt){
            input.change(e => {
                evt(e.currentTarget)
            })
            input.keydown((e)=>e.preventDefault())
        }

        return {element: element, input: input, event: setEvent}
    }

    return {
        customDateRangeUIHook: customDateRangeUIHook
    }
})