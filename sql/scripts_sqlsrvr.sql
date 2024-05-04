if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'INVOICE_DETAILS')
    drop table INVOICE_DETAILS
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'INVOICES')
    drop table INVOICES
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'PRODUCTS_ADDED')
    drop table PRODUCTS_ADDED
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'PUBLISH_PRODUCT')
    drop table PUBLISH_PRODUCT
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'USERS')
    drop table USERS
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'SHOPPING_CARS')
    drop table SHOPPING_CARS
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'PERSONS')
    drop table PERSONS
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'MEASUREMENT')
    drop table MEASUREMENT
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'PRODUCTS')
    drop table PRODUCTS
go

if exists (select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'CATEGORIES')
    drop table CATEGORIES
go

create table CATEGORIES (
   ID_CATEGORIE         int                  not null identity(1,1),
   NAME_CATEGORIE       varchar(100)         not null,
   constraint PK_CATEGORIES primary key nonclustered (ID_CATEGORIE)
)
go

create table INVOICES (
   ID_INVOICE           int                  not null identity(1,1),
   INVOICE_DATE         datetime             not null,
   PAYMENT_METHOD       varchar(100)         not null,
   constraint PK_INVOICES primary key nonclustered (ID_INVOICE)
)
go

create table INVOICE_DETAILS (
   ID_INVOICE_DET       int                  not null identity(1,1),
   ID_PUBLISH_PROD      int                  not null,
   ID_INVOICE           int                  not null,
   ID_USER              int                  not null,
   PROD_QUANTITY        int                  not null,
   UNIT_VALUE_PROD      float                not null,
   SUBTOTAL             float                not null,
   TOTAL                float                not null,
   constraint PK_INVOICE_DETAILS primary key nonclustered (ID_INVOICE_DET)
)
go

create table MEASUREMENT (
   ID_MEASURE_PROD      int                  not null identity(1,1),
   NAME_MEASURE         varchar(100)         not null,
   constraint PK_MEASUREMENT primary key nonclustered (ID_MEASURE_PROD)
)
go

create table PERSONS (
   ID_PERSON            int                  not null identity(1,1),
   FIRST_NAME           varchar(100)         not null,
   LAST_NAME            varchar(100)         not null,
   DOC_TYPE             varchar(50)          not null,
   DOC_NUMBER           varchar(50)          not null,
   PHONE_NUMBER         varchar(50)          not null,
   LOCATION             varchar(50)          not null,
   constraint PK_PERSONS primary key nonclustered (ID_PERSON)
)
go

create table PRODUCTS (
   ID_PRODUCT           int                  not null identity(1,1),
   ID_CATEGORIE         int                  not null,
   ID_MEASURE_PROD      int                  not null,
   PRODUCT_NAME         varchar(100)         not null,
   UNIT_VALUE           float                not null,
   QUANTITY             float                not null,
   DESCRIPTION          varchar(255)         not null,
   LOCATION             varchar(100)         not null,
   IMAGE                varchar(255)         not null,
   constraint PK_PRODUCTS primary key nonclustered (ID_PRODUCT)
)
go

create table PRODUCTS_ADDED (
   ID_SHOP_CAR          int                  not null identity(1,1),
   ID_PUBLISH_PROD      int                  not null,
   constraint PK_PRODUCTS_ADDED primary key nonclustered (ID_SHOP_CAR, ID_PUBLISH_PROD)
)
go

create table PUBLISH_PRODUCT (
   ID_PUBLISH_PROD      int                  not null identity(1,1),
   ID_PRODUCT           int                  not null,
   ID_USER              int                  not null,
   constraint PK_PUBLISH_PRODUCT primary key nonclustered (ID_PUBLISH_PROD)
)
go

create table SHOPPING_CARS (
   ID_SHOP_CAR          int                  not null identity(1,1),
   constraint PK_SHOPPING_CARS primary key nonclustered (ID_SHOP_CAR)
)
go

create table USERS (
   ID_USER              int                  not null identity(1,1),
   ID_PERSON            int                  not null,
   PASSWORD             varchar(100)         not null,
   EMAIL                varchar(100)         not null,
   CREDIT_NUMBER        varchar(50)          not null,
   IS_ADMIN             int                  not null,
   constraint PK_USERS primary key nonclustered (ID_USER)
)
go

alter table INVOICE_DETAILS
   add constraint FK_INVOICE_IDINV_FK_INVOICES foreign key (ID_INVOICE)
      references INVOICES (ID_INVOICE)
go

alter table INVOICE_DETAILS
   add constraint FK_INVOICE_IDPUBPROD_PUBLISH foreign key (ID_PUBLISH_PROD)
      references PUBLISH_PRODUCT (ID_PUBLISH_PROD)
go

alter table INVOICE_DETAILS
   add constraint FK_INVOICE__IDUSER_FK_USERS foreign key (ID_USER)
      references USERS (ID_USER)
go

alter table PRODUCTS
   add constraint FK_PRODUCTS_IDCAT_FK__CATEGORI foreign key (ID_CATEGORIE)
      references CATEGORIES (ID_CATEGORIE)
go

alter table PRODUCTS
   add constraint FK_PRODUCTS_IDMEAS_FK_MEASUREM foreign key (ID_MEASURE_PROD)
      references MEASUREMENT (ID_MEASURE_PROD)
go

alter table PRODUCTS_ADDED
   add constraint FK_PRODUCTS_RELATIONS_SHOPPING foreign key (ID_SHOP_CAR)
      references SHOPPING_CARS (ID_SHOP_CAR)
go

alter table PRODUCTS_ADDED
   add constraint FK_PRODUCTS_RELATIONS_PUBLISH_ foreign key (ID_PUBLISH_PROD)
      references PUBLISH_PRODUCT (ID_PUBLISH_PROD)
go

alter table PUBLISH_PRODUCT
   add constraint FK_PUBLISH__IDPROD_FK_PRODUCTS foreign key (ID_PRODUCT)
      references PRODUCTS (ID_PRODUCT)
go

alter table PUBLISH_PRODUCT
   add constraint FK_PUBLISH__IDUSER_FK_USERS foreign key (ID_USER)
      references USERS (ID_USER)
go

alter table USERS
   add constraint FK_USERS_IDPER_FK__PERSONS foreign key (ID_PERSON)
      references PERSONS (ID_PERSON)
go
