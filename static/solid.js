'use strict';

$(window).scroll(function() {
    if ($(window).scrollTop() >= 50) {
      $('.navbar').css('background', '#F1EFE7');
    } else {
      $('.navbar').css('background', 'transparent');
    }
  });