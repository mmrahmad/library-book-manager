(function () {
  'use strict';

  angular
    .module('libraryApp')
    .controller('BookFormController', ['BookService', '$routeParams', '$location',
      function (BookService, $routeParams, $location) {
        var vm = this;

        vm.isEdit = !!$routeParams.id;
        vm.book = { title: '', author: '', category: '', published_year: null };
        vm.categories = [];
        vm.minYear = 1900;
        vm.maxYear = new Date().getFullYear();
        vm.loading = false;
        vm.saving = false;
        vm.error = null;

        vm.save = save;
        vm.cancel = cancel;
        vm.showError = showError;

        BookService.categories()
          .then(function (categories) { vm.categories = categories; })
          .catch(function () { /* suggestions only; not critical */ });

        if (vm.isEdit) {
          vm.loading = true;
          BookService.get($routeParams.id)
            .then(function (book) {
              vm.book = {
                title: book.title,
                author: book.author,
                category: book.category || '',
                published_year: book.published_year
              };
            })
            .catch(function (message) { vm.error = message; vm.loadFailed = true; })
            .finally(function () { vm.loading = false; });
        }

        // Show a field's error once the user has touched it or tried to submit.
        function showError(form, field) {
          var control = form[field];
          return control && control.$invalid && (control.$touched || form.$submitted);
        }

        function save(form) {
          if (form.$invalid) { return; }
          vm.saving = true;
          vm.error = null;
          var request = vm.isEdit
            ? BookService.update($routeParams.id, vm.book)
            : BookService.create(vm.book);
          request
            .then(function () { $location.path('/books'); })
            .catch(function (message) { vm.error = message; })
            .finally(function () { vm.saving = false; });
        }

        function cancel() {
          $location.path('/books');
        }
      }]);
})();
