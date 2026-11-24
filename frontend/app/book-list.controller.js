(function () {
  'use strict';

  angular
    .module('libraryApp')
    .controller('BookListController', ['BookService', '$window', function (BookService, $window) {
      var vm = this;

      vm.books = [];
      vm.categories = [];
      vm.filters = { search: '', category: '', sort: 'created_at', order: 'desc' };
      vm.page = 1;
      vm.perPage = 10;
      vm.total = 0;
      vm.pages = 0;
      vm.loading = false;
      vm.error = null;
      vm.notice = null;
      vm.busyId = null;            // id of the book whose action is in flight
      vm.borrowTarget = null;      // book currently in the borrow dialog
      vm.borrowerName = '';
      vm.borrowError = null;

      vm.load = load;
      vm.onFilterChange = onFilterChange;
      vm.goToPage = goToPage;
      vm.sortBy = sortBy;
      vm.openBorrow = openBorrow;
      vm.closeBorrow = closeBorrow;
      vm.confirmBorrow = confirmBorrow;
      vm.giveBack = giveBack;
      vm.remove = remove;

      load();
      loadCategories();

      function load() {
        vm.loading = true;
        vm.error = null;
        var params = {
          search: vm.filters.search || undefined,
          category: vm.filters.category || undefined,
          sort: vm.filters.sort,
          order: vm.filters.order,
          page: vm.page,
          per_page: vm.perPage
        };
        return BookService.list(params)
          .then(function (data) {
            vm.books = data.items;
            vm.total = data.total;
            vm.pages = data.pages;
            // Deleting the last book on a page leaves it empty: step back.
            if (vm.books.length === 0 && vm.page > 1) {
              vm.page -= 1;
              return load();
            }
          })
          .catch(function (message) { vm.error = message; })
          .finally(function () { vm.loading = false; });
      }

      function loadCategories() {
        BookService.categories()
          .then(function (categories) { vm.categories = categories; })
          .catch(function () { /* list call already reports connectivity errors */ });
      }

      function onFilterChange() {
        vm.page = 1;
        load();
      }

      function goToPage(page) {
        if (page < 1 || page > vm.pages || page === vm.page) { return; }
        vm.page = page;
        load();
      }

      function sortBy(field) {
        if (vm.filters.sort === field) {
          vm.filters.order = vm.filters.order === 'asc' ? 'desc' : 'asc';
        } else {
          vm.filters.sort = field;
          vm.filters.order = 'asc';
        }
        onFilterChange();
      }

      function openBorrow(book) {
        vm.borrowTarget = book;
        vm.borrowerName = '';
        vm.borrowError = null;
      }

      function closeBorrow() {
        vm.borrowTarget = null;
      }

      function confirmBorrow(form) {
        if (form.$invalid) { return; }
        var book = vm.borrowTarget;
        vm.busyId = book.id;
        vm.borrowError = null;
        BookService.borrow(book.id, vm.borrowerName)
          .then(function (updated) {
            angular.extend(book, updated);
            vm.notice = '"' + book.title + '" borrowed by ' + updated.borrower_name + '.';
            closeBorrow();
          })
          .catch(function (message) { vm.borrowError = message; })
          .finally(function () { vm.busyId = null; });
      }

      function giveBack(book) {
        vm.busyId = book.id;
        vm.error = null;
        BookService.giveBack(book.id)
          .then(function (updated) {
            angular.extend(book, updated);
            vm.notice = '"' + book.title + '" returned.';
          })
          .catch(function (message) { vm.error = message; })
          .finally(function () { vm.busyId = null; });
      }

      function remove(book) {
        if (!$window.confirm('Delete "' + book.title + '"? This cannot be undone.')) { return; }
        vm.busyId = book.id;
        vm.error = null;
        BookService.remove(book.id)
          .then(function () {
            vm.notice = '"' + book.title + '" deleted.';
            load();
            loadCategories();
          })
          .catch(function (message) { vm.error = message; })
          .finally(function () { vm.busyId = null; });
      }
    }]);
})();
