(function () {
  'use strict';

  angular
    .module('libraryApp', ['ngRoute'])
    .constant('API_URL', window.LIBRARY_CONFIG.apiUrl)
    .config(['$routeProvider', function ($routeProvider) {
      $routeProvider
        .when('/books', {
          templateUrl: 'app/views/book-list.html',
          controller: 'BookListController',
          controllerAs: 'vm'
        })
        .when('/books/new', {
          templateUrl: 'app/views/book-form.html',
          controller: 'BookFormController',
          controllerAs: 'vm'
        })
        .when('/books/:id/edit', {
          templateUrl: 'app/views/book-form.html',
          controller: 'BookFormController',
          controllerAs: 'vm'
        })
        .otherwise({ redirectTo: '/books' });
    }]);
})();
