/* Read the Docs - Documentation promotions */

var constants = require('./doc-embed/constants');

module.exports = {
    Promo: Promo
};

function Promo (id, text, link, image, theme, display_type) {
    this.id = id;
    this.text = text;
    this.link = link;
    this.image = image;
    this.theme = theme || constants.THEME_RTD;
    this.display_type = display_type || constants.PROMO_TYPES.LEFTNAV;
    this.promo = null;

    // Handler when a promo receives a click
    this.click_handler = function () {
        if (_gaq) {
            _gaq.push(
                ['rtfd._setAccount', 'UA-17997319-1'],
                ['rtfd._trackEvent', 'Promo', 'Click', self.id]
            );
        }
    };
}

Promo.prototype.create = function () {
    var self = this,
        menu,
        promo_class;
    if (this.theme == constants.THEME_RTD) {
        menu = this.get_sphinx_rtd_theme_promo_selector();
        promo_class = this.display_type === constants.PROMO_TYPES.FOOTER ? 'rtd-pro-footer' : 'wy-menu';
    }
    else if (this.theme == constants.THEME_ALABASTER) {
        menu = this.get_alabaster_promo_selector();
        promo_class = this.display_type === constants.PROMO_TYPES.FOOTER ? 'rtd-pro-footer' : 'alabaster';
    }

    if (typeof(menu) != 'undefined') {
        this.place_promo(menu, promo_class);
    }
}

Promo.prototype.place_promo = function (selector, promo_class) {
    var self = this;

    // Add elements
    var promo = $('<div />')
        .attr('class', 'rtd-pro ' + promo_class);

    // Promo info
    var promo_about = $('<div />')
        .attr('class', 'rtd-pro-about');
    var promo_about_link = $('<a />')
        .attr('href', 'https://readthedocs.org/sustainability/advertising/')
        .appendTo(promo_about);
    $('<span />').text('Sponsored ').appendTo(promo_about_link);
    var promo_about_icon = $('<i />')
        .attr('class', 'fa fa-info-circle')
        .appendTo(promo_about_link);
    promo_about.appendTo(promo);

    // Promo image
    if (self.image) {
        var promo_image_link = $('<a />')
            .attr('class', 'rtd-pro-image-wrapper')
            .attr('href', self.link)
            .attr('target', '_blank')
            .on('click', this.click_handler);
        var promo_image = $('<img />')
            .attr('class', 'rtd-pro-image')
            .attr('src', self.image)
            .appendTo(promo_image_link);
        promo.append(promo_image_link);
    }

    // Create link with callback
    var promo_text = $('<span />')
        .html(self.text);
    $(promo_text).find('a').each(function () {
        $(this)
            .attr('class', 'rtd-pro-link')
            .attr('href', self.link)
            .attr('target', '_blank')
            .on('click', this.click_handler);
    });
    promo.append(promo_text);

    var copy_text = $(
    '<p class="ethical-callout"><small><em><a href="https://docs.readthedocs.io/en/latest/ethical-advertising.html">' +
    'Ads served ethically' +
    '</a></em></small></p>'
    )
    promo.append(copy_text);


    promo.appendTo(selector);

    promo.wrapper = $('<div />')
        .attr('class', 'rtd-pro-wrapper')
        .appendTo(selector);

    return promo;
};

Promo.prototype.get_alabaster_promo_selector = function () {
    // Return a jQuery selector where the promo goes on the Alabaster theme
    var self = this,
        selector;

    if (self.display_type === constants.PROMO_TYPES.FOOTER) {
        selector = $('<div />')
            .attr('class', 'rtd-pro-footer-wrapper body')
            .appendTo('div.bodywrapper');
        $('<hr />').insertBefore(selector);
        $('<hr />').insertAfter(selector);
    } else {
        selector = $('div.sphinxsidebar > div.sphinxsidebarwrapper');
    }

    if (selector.length) {
        return selector;
    }
};


Promo.prototype.get_sphinx_rtd_theme_promo_selector = function () {
    // Return a jQuery selector where the promo goes on the RTD theme
    var self = this,
        selector;

    if (self.display_type === constants.PROMO_TYPES.FOOTER) {
        selector = $('<div />')
            .attr('class', 'rtd-pro-footer-wrapper')
            .insertBefore('footer hr');
        $('<hr />').insertBefore(selector);
    } else {
        selector = $('nav.wy-nav-side > div.wy-side-scroll');
    }

    if (selector.length) {
        return selector;
    }
};

// Position promo
Promo.prototype.display = function () {
    var promo = this.promo,
        self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }

    // Promo still might not exist yet
    if (promo) {
        promo.show();
    }
};

Promo.prototype.disable = function () {
};

// Variant factory method
Promo.from_variants = function (variants) {
    if (variants.length == 0) {
        return null;
    }
    var chosen = Math.floor(Math.random() * variants.length),
        variant = variants[chosen],
        text = variant.text,
        link = variant.link,
        image = variant.image,
        id = variant.id;
    return new Promo(id, text, link, image);
};
