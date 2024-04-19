'use strict';

const ctaLink = document.querySelector(".shop");

ctaLink.addEventListener("click", function (event) {
  event.preventDefault();

  const targetSection = document.querySelector("#shop");
  targetSection.scrollIntoView({ behavior: "smooth" });
});
