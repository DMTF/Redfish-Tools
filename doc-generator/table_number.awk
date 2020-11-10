BEGIN		{
		table_count = TABLES;
		figure_count = FIGURES;
		doc_version = VERSION;
		doc_date = DATE;
		doc_year = YEAR;
		doc_type = TYPE;
       	}
$0 ~ /TBL_nn\+\+/	{ 	table_count = table_count + 1; 
			gsub(/TBL_nn\+\+/, "TBL_nn", $0) ;
		}
$0 ~ /TBL_nn/	{ 
			tag = "" table_count;
			gsub(/TBL_nn/, tag, $0 ) ;
		}
$0 ~ /FIG_nn\+\+/	{ 	figure_count = figure_count + 1; 
			gsub(/FIG_nn\+\+/, "FIG_nn", $0) ;
		}
$0 ~ /FIG_nn/	{ 
			tag = "" figure_count;
			gsub(/FIG_nn/, tag, $0 ) ;
		}
$0 ~ /DOC_VERSION/	{ 
			tag = "" doc_version
			gsub(/DOC_VERSION/, tag, $0 ) ;
		}
$0 ~ /DOC_TYPE/	{ 
			tag = "" doc_type
			gsub(/DOC_TYPE/, tag, $0 ) ;
		}
$0 ~ /DOC_DATE/	{ 
			tag = "" doc_date
			gsub(/DOC_DATE/, tag, $0 ) ;
		}
$0 ~ /DOC_YEAR/	{ 
			tag = "" doc_year
			gsub(/DOC_YEAR/, tag, $0 ) ;
		}
		{print}
END		{
		print table_count > "__TABLES";
		print figure_count > "__FIGURES";
       	}
