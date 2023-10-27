var SPMaskBehavior = function (val) {
    return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
},
    spOptions = {
        onKeyPress: function (val, e, field, options) {
            field.mask(SPMaskBehavior.apply({}, arguments), options);
        }
    };

$(function () {
    $('.mask-telefone').mask(SPMaskBehavior, spOptions);
    $('.mask-cpf').mask('000.000.000-00', { reverse: true });
    $('.mask-rg').mask('00.000.000-00', { reverse: true });

    
});

document.getElementById("mostrar_select").addEventListener("change",function(){
    document.getElementById('mostrar').submit()
})