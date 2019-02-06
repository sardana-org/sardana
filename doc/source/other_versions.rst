
===============================
Docs for other Sardana versions
===============================

The `main sardana docs <http://sardana-controls.org>`_ are generated for the
most recent development version.

But docs for other versions of sardana (previous releases or other branches in
`repository <https://github.com/sardana-org/sardana>`_ can also be browsed here:


.. raw:: html

   <!-- Create a list of links to builds of the docs for other branches -->
   <div class="container">
      <div class="row">
         <div class="col-sm">
            <table class="table">
              <tbody class="tb"></tbody>
            </table>
         </div>
      </div>
   </div>

   <script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>

   <script>
      // TODO: once the DNS gets pointed to github pages instead of RTD, the doc_url can be changed to "http://sardana-controls.org/"
      var doc_url = "https://sardana-org.github.io/sardana-doc/";
      var contents_url = "https://api.github.com/repos/sardana-org/sardana-doc/contents/./";

      function list_items(url){
         $.ajax({url: url}).then(function(data) {
            $('.tb').html('');
            $('.tb').append('<tr><td><a target="_blank" href="' + doc_url + '">' + 'develop' + '</a></td></tr>');
            data.forEach(function(element) {
               if (element.name.match(/^v-/)) {
                  $('.tb').append('<tr><td><a target="_blank" href="' + doc_url + element.name + '">' + element.name.slice(2) + '</a></td></tr>');
               };
            });
         });
      }

      $(document).ready(function() {
         list_items(contents_url);
      });
   </script>


