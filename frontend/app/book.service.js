(function () {
  'use strict';

  /**
   * BookService: the only place that talks to the API.
   * Every method returns a promise that resolves with the response body,
   * or rejects with a human-readable error message string.
   */
  angular
    .module('libraryApp')
    .factory('BookService', ['$http', '$q', 'API_URL', function ($http, $q, API_URL) {

      function unwrap(response) {
        return response.data;
      }

      function toMessage(response) {
        var message;
        if (response.status <= 0) {
          message = 'Cannot reach the server. Is the backend running at ' + API_URL + '?';
        } else if (response.data && response.data.error) {
          message = response.data.error;
        } else {
          message = 'Request failed (HTTP ' + response.status + ')';
        }
        return $q.reject(message);
      }

      function bookUrl(id) {
        return API_URL + '/books/' + encodeURIComponent(id);
      }

      return {
        list: function (params) {
          return $http.get(API_URL + '/books', { params: params }).then(unwrap, toMessage);
        },
        categories: function () {
          return $http.get(API_URL + '/categories').then(unwrap, toMessage);
        },
        get: function (id) {
          return $http.get(bookUrl(id)).then(unwrap, toMessage);
        },
        create: function (book) {
          return $http.post(API_URL + '/books', book).then(unwrap, toMessage);
        },
        update: function (id, book) {
          return $http.put(bookUrl(id), book).then(unwrap, toMessage);
        },
        remove: function (id) {
          return $http.delete(bookUrl(id)).then(unwrap, toMessage);
        },
        borrow: function (id, borrowerName) {
          return $http.post(bookUrl(id) + '/borrow', { borrower_name: borrowerName }).then(unwrap, toMessage);
        },
        giveBack: function (id) {
          return $http.post(bookUrl(id) + '/return').then(unwrap, toMessage);
        }
      };
    }]);
})();
