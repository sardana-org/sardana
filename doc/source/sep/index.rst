Sardana Enhancement Proposals
=============================

.. raw:: html

    <script>
    //Function to redirect to the SEPs website
    function redirect()
    {
        // Base url: URL where are hosted the SEPs
        var baseurl = "https://github.com/sardana-org/sardana/tree/develop/doc/source/sep/"
        // Get query if exist:
        var query = location.search.substring(1)
        if (typeof query === 'undefined' || !query)
        {
            // If there is not a query redirect to the index page
            query = "index.md"
        }
        var url = baseurl.concat(query);
        window.location = url;
    }
    redirect()
    </script>
